"""StorageHandler para FTP."""

from __future__ import annotations

import logging
from ftplib import FTP, all_errors, error_perm
from pathlib import Path

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


class FTPStorageHandler(StorageHandler):
    """Sube y elimina archivos en un servidor FTP."""

    def _get_client(self) -> FTP:
        ftp = FTP()
        ftp.connect(settings.FTP_HOST, settings.FTP_PORT, timeout=10)
        ftp.login(settings.FTP_USER, settings.FTP_PASS)
        ftp.set_pasv(True)
        ftp.cwd(settings.FTP_DIR)
        return ftp

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        ftp = None
        safe_name = self._validate_filename(filename)

        try:
            ftp = self._get_client()
            with open(temp_path, "rb") as file_obj:
                ftp.storbinary(f"STOR {safe_name}", file_obj)

            base_dir = settings.FTP_DIR.rstrip("/")
            saved_path = f"ftp://{settings.FTP_HOST}:{settings.FTP_PORT}{base_dir}/{safe_name}"
            logger.info("FTPStorage save OK '%s' -> %s", safe_name, saved_path)
            return saved_path
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        ftp = None
        safe_name = self._validate_filename(filename)

        try:
            ftp = self._get_client()
            ftp.delete(safe_name)
            logger.info("FTPStorage delete OK '%s'", safe_name)
        except error_perm as exc:
            message = str(exc)
            upper_message = message.upper()

            if message.startswith("530"):
                raise StorageAuthenticationError(
                    "Autenticacion FTP rechazada. Verifica las credenciales configuradas."
                ) from exc
            if message.startswith("550"):
                if "NO SUCH FILE" in upper_message or "NOT FOUND" in upper_message:
                    logger.info("FTPStorage delete skipped '%s' because remote file was absent", safe_name)
                    return
                raise StoragePermissionError(
                    "FTP rechazo la eliminacion del archivo. Verifica permisos sobre el directorio remoto."
                ) from exc
            raise StorageConfigurationError(f"Error FTP al eliminar '{safe_name}': {exc}") from exc
        except all_errors as exc:
            raise StorageConfigurationError(f"Error FTP al eliminar '{safe_name}': {exc}") from exc
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass

    def _validate_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo FTP es invalido. No se permiten rutas embebidas ni '..'."
            )
        return safe_name
