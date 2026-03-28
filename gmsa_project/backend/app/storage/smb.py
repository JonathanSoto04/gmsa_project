"""
storage/smb.py
--------------
StorageHandler para SMB (Samba / Windows Share / TrueNAS).

Usa credenciales del request cuando se proporcionan y, si no existen,
recurre a la configuracion del entorno. Ademas valida la ruta remota,
registra eventos relevantes y traduce errores SMB comunes a excepciones
de dominio mas claras.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path, PurePosixPath

import smbclient
import smbprotocol.connection

from app.config import settings
from app.storage.base import (
    StorageAuthenticationError,
    StorageConfigurationError,
    StorageCredentials,
    StorageHandler,
    StoragePathError,
    StoragePermissionError,
)

logger = logging.getLogger(__name__)


class SMBStorageHandler(StorageHandler):
    """Sube archivos a un share SMB."""

    def _resolve_credentials(self, credentials: StorageCredentials | None) -> StorageCredentials:
        username = credentials.username.strip() if credentials and credentials.username else settings.SMB_USER
        password = credentials.password if credentials and credentials.password else settings.SMB_PASS

        if not username or not password:
            raise StorageConfigurationError(
                "SMB requiere credenciales validas. Define SMB_USER/SMB_PASS o envialas en el request."
            )

        domain = settings.SMB_DOMAIN.strip()
        if domain and "\\" not in username and "@" not in username:
            username = f"{domain}\\{username}"

        return StorageCredentials(username=username, password=password)

    def _register_session(self, credentials: StorageCredentials) -> None:
        smbprotocol.connection.MAX_PAYLOAD_SIZE = 1048576
        smbclient.ClientConfig(
            username=credentials.username,
            password=credentials.password,
            require_secure_negotiate=False,
        )
        smbclient.reset_connection_cache()  # ← fuerza sesión nueva cada vez
        try:
            smbclient.register_session(
                settings.SMB_HOST,
                username=credentials.username,
                password=credentials.password,
                encrypt=False,
                require_signing=False,
            )
        except Exception:
            pass
    def _validate_filename(self, filename: str) -> str:
        if not filename:
            raise StoragePathError("El archivo SMB no tiene un nombre valido.")

        safe_name = Path(filename).name
        if safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo SMB es invalido. No se permiten rutas embebidas ni '..'."
            )
        return safe_name

    def _build_remote_paths(self, filename: str) -> tuple[str, str]:
        share = settings.SMB_SHARE.strip().strip("/\\")
        if not settings.SMB_HOST.strip():
            raise StorageConfigurationError("SMB_HOST no esta configurado.")
        if not share:
            raise StorageConfigurationError("SMB_SHARE no esta configurado.")

        relative_dir = str(PurePosixPath("/", settings.SMB_DIR.strip() or "/")).strip("/")
        share_root   = f"//{settings.SMB_HOST}/{share}"
        remote_dir   = f"{share_root}/{relative_dir}" if relative_dir else share_root
        remote_path  = f"{remote_dir}/{filename}"     if relative_dir else f"{share_root}/{filename}"
        return remote_dir, remote_path

    def _ensure_remote_directory(self, remote_dir: str) -> None:
        try:
            smbclient.makedirs(remote_dir, exist_ok=True)
        except AttributeError:
            logger.debug("smbclient.makedirs no esta disponible; se omite creacion de directorio.")
        except Exception as exc:
            raise self._map_smb_error(
                exc,
                default_message=(
                    f"No fue posible preparar el directorio remoto SMB '{remote_dir}'. "
                    "Revisa que el share y la carpeta existan y permitan escritura."
                ),
            ) from exc

    def _map_smb_error(self, exc: Exception, default_message: str) -> Exception:
        text = str(exc).upper()
        if "STATUS_LOGON_FAILURE" in text or "STATUS_ACCOUNT_RESTRICTION" in text:
            return StorageAuthenticationError(
                "Autenticacion SMB rechazada. Verifica usuario, contrasena y dominio."
            )
        if "STATUS_ACCESS_DENIED" in text:
            return StoragePermissionError(
                "SMB autentico la sesion pero el usuario no tiene permisos de escritura "
                f"sobre el share '{settings.SMB_SHARE}' o la carpeta '{settings.SMB_DIR}'."
            )
        if any(s in text for s in (
            "STATUS_BAD_NETWORK_NAME", "STATUS_OBJECT_PATH_NOT_FOUND",
            "STATUS_OBJECT_NAME_NOT_FOUND", "STATUS_NOT_A_DIRECTORY",
        )):
            return StoragePathError(
                "La ruta SMB no existe o no es accesible. "
                f"Revisa SMB_SHARE='{settings.SMB_SHARE}' y SMB_DIR='{settings.SMB_DIR}'."
            )
        return StorageConfigurationError(default_message)

    def save(self, temp_path: Path, filename: str, credentials: StorageCredentials | None = None) -> str:
        safe_filename = re.sub(r'[\s\(\)\[\]\{\}]', '_', filename)
        safe_filename = re.sub(r'_+', '_', safe_filename)

        contents = temp_path.read_bytes()
        creds = self._resolve_credentials(credentials)
        self._register_session(creds)

        remote_path = f"//{settings.SMB_HOST}/{settings.SMB_SHARE}/{safe_filename}"

        try:
            with smbclient.open_file(remote_path, mode="wb") as f:
                f.write(contents)
        except Exception as exc:
            raise self._map_smb_error(
                exc,
                default_message=f"Error SMB no controlado al escribir '{filename}' en '{remote_path}'.",
            ) from exc

        logger.info("SMBStorage: '%s' → %s", filename, remote_path)
        return remote_path