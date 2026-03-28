"""
storage/smb.py
--------------
StorageHandler para SMB (Samba / Windows Share / TrueNAS).

Mantiene una sola implementacion consistente para autenticacion, validacion
de ruta y escritura remota. Tambien traduce los errores SMB mas comunes a
mensajes de dominio que la capa de servicios puede devolver al cliente.
"""

from __future__ import annotations

import logging
from pathlib import Path

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
        smbclient.reset_connection_cache()

        logger.info(
            "SMB connect host=%s share=%s user=%s",
            settings.SMB_HOST,
            settings.SMB_SHARE,
            credentials.username,
        )

        smbclient.register_session(
            settings.SMB_HOST,
            username=credentials.username,
            password=credentials.password,
            encrypt=False,
            require_signing=False,
        )

    def _validate_filename(self, filename: str) -> str:
        if not filename:
            raise StoragePathError("El archivo SMB no tiene un nombre valido.")

        safe_name = Path(filename).name
        if safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo SMB es invalido. No se permiten rutas embebidas ni '..'."
            )

        return safe_name

    def _build_remote_path(self, filename: str) -> str:
        host = settings.SMB_HOST.strip()
        share = settings.SMB_SHARE.strip().strip("/\\")

        if not host:
            raise StorageConfigurationError("SMB_HOST no esta configurado.")
        if not share:
            raise StorageConfigurationError("SMB_SHARE no esta configurado.")

        return f"//{host}/{share}/{filename}"

    def _map_smb_error(self, exc: Exception, default_message: str) -> Exception:
        text = str(exc).upper()

        if "STATUS_LOGON_FAILURE" in text or "STATUS_ACCOUNT_RESTRICTION" in text:
            return StorageAuthenticationError(
                "Autenticacion SMB rechazada. Verifica usuario, contrasena y dominio."
            )

        if "STATUS_ACCESS_DENIED" in text:
            return StoragePermissionError(
                "SMB autentico la sesion pero el usuario no tiene permisos de escritura "
                f"sobre el share '{settings.SMB_SHARE}'."
            )

        if (
            "STATUS_BAD_NETWORK_NAME" in text
            or "STATUS_OBJECT_PATH_NOT_FOUND" in text
            or "STATUS_OBJECT_NAME_NOT_FOUND" in text
            or "STATUS_NOT_A_DIRECTORY" in text
        ):
            return StoragePathError(
                "La ruta SMB no existe o no es accesible. "
                f"Revisa SMB_SHARE='{settings.SMB_SHARE}'."
            )

        if "SIGNING" in text or "NEGOTIATE" in text or "DIALECT" in text:
            return StorageConfigurationError(
                "La negociacion SMB fue rechazada por el servidor. "
                "Es posible que el servidor requiera signing, secure negotiate o una politica SMB distinta."
            )

        return StorageConfigurationError(default_message)

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        safe_name = self._validate_filename(filename)
        resolved_credentials = self._resolve_credentials(credentials)
        remote_path = self._build_remote_path(safe_name)

        try:
            self._register_session(resolved_credentials)

            logger.info("SMB write start path=%s", remote_path)
            with smbclient.open_file(remote_path, mode="wb") as remote_file:
                with open(temp_path, "rb") as local_file:
                    while chunk := local_file.read(1024 * 1024):
                        remote_file.write(chunk)

            logger.info("SMB write OK '%s' -> %s", safe_name, remote_path)
            return remote_path

        except (StorageAuthenticationError, StorageConfigurationError, StoragePathError, StoragePermissionError):
            raise
        except Exception as exc:
            logger.exception(
                "SMB write failed for '%s' on %s (%s: %r)",
                safe_name,
                remote_path,
                type(exc).__name__,
                exc,
            )
            raise self._map_smb_error(
                exc,
                default_message=f"Error SMB no controlado al escribir '{safe_name}' en '{remote_path}'.",
            ) from exc
