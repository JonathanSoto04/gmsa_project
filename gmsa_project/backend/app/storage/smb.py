"""StorageHandler para SMB."""

from __future__ import annotations

import logging
from datetime import datetime
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
    """Sube, lista y elimina archivos en un share SMB."""

    def _resolve_credentials(self, credentials: StorageCredentials | None) -> StorageCredentials:
        username = settings.SMB_USER
        password = settings.SMB_PASS

        if not username or not password:
            raise StorageConfigurationError(
                "SMB requiere credenciales validas en la configuracion. Define SMB_USER/SMB_PASS en .env."
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
        smbclient.register_session(
            settings.SMB_HOST,
            username=credentials.username,
            password=credentials.password,
            encrypt=False,
            require_signing=False,
        )

    def _validate_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or safe_name in {".", ".."}:
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
                "SMB autentico la sesion pero el usuario no tiene permisos sobre el share configurado."
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
                "Es posible que el servidor requiera una politica SMB distinta."
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
        contents = temp_path.read_bytes()

        try:
            self._register_session(resolved_credentials)
            with smbclient.open_file(remote_path, mode="wb") as remote_file:
                remote_file.write(contents)
            logger.info("SMBStorage save OK '%s' -> %s", safe_name, remote_path)
            return remote_path
        except (StorageAuthenticationError, StorageConfigurationError, StoragePathError, StoragePermissionError):
            raise
        except Exception as exc:
            logger.exception(
                "SMB save failed for '%s' on %s (%s: %r)",
                safe_name, remote_path, type(exc).__name__, exc,
            )
            raise self._map_smb_error(
                exc,
                default_message=f"Error SMB no controlado al escribir '{safe_name}' en '{remote_path}'.",
            ) from exc

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        safe_name = self._validate_filename(filename)
        resolved_credentials = self._resolve_credentials(credentials)
        remote_path = self._build_remote_path(safe_name)

        try:
            self._register_session(resolved_credentials)
            smbclient.remove(remote_path)
            logger.info("SMBStorage delete OK '%s' -> %s", safe_name, remote_path)
        except FileNotFoundError:
            logger.info("SMBStorage delete skipped '%s' because remote file was absent", safe_name)
        except (StorageAuthenticationError, StorageConfigurationError, StoragePathError, StoragePermissionError):
            raise
        except Exception as exc:
            text = str(exc).upper()
            if "STATUS_OBJECT_NAME_NOT_FOUND" in text or "STATUS_OBJECT_PATH_NOT_FOUND" in text:
                logger.info("SMBStorage delete skipped '%s' because remote file was absent", safe_name)
                return
            logger.exception(
                "SMB delete failed for '%s' on %s (%s: %r)",
                safe_name, remote_path, type(exc).__name__, exc,
            )
            raise self._map_smb_error(
                exc,
                default_message=f"Error SMB no controlado al eliminar '{safe_name}' en '{remote_path}'.",
            ) from exc

    def list_files(
        self,
        credentials: StorageCredentials | None = None,
    ) -> list[dict]:
        resolved_credentials = self._resolve_credentials(credentials)
        share_root = self._build_remote_path("")
        items: list[dict] = []

        try:
            self._register_session(resolved_credentials)
            for entry in smbclient.scandir(share_root):
                if not entry.is_file():
                    continue

                stat_result = entry.stat()
                modified = datetime.fromtimestamp(stat_result.st_mtime).isoformat(timespec="seconds")
                items.append(
                    {
                        "name": entry.name,
                        "protocol": "smb",
                        "size": int(stat_result.st_size),
                        "path": self._build_remote_path(entry.name),
                        "created_at": modified,
                        "modified_at": modified,
                    }
                )

            return sorted(items, key=lambda item: item["modified_at"], reverse=True)
        except (StorageAuthenticationError, StorageConfigurationError, StoragePathError, StoragePermissionError):
            raise
        except Exception as exc:
            logger.exception("SMB list failed on %s (%s: %r)", share_root, type(exc).__name__, exc)
            raise self._map_smb_error(
                exc,
                default_message=f"Error SMB no controlado al listar archivos en '{share_root}'.",
            ) from exc
