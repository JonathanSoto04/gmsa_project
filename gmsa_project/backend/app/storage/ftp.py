"""
storage/ftp.py
--------------
StorageHandler para FTP.

Lee credenciales desde settings (que a su vez las carga del .env).
Abre una conexión FTP en modo pasivo, sube el archivo con STOR
y cierra la conexión de forma garantizada en el bloque finally.
"""

from __future__ import annotations

import logging
from ftplib import FTP
from pathlib import Path

from app.config import settings
from app.storage.base import StorageCredentials, StorageHandler

logger = logging.getLogger(__name__)


class FTPStorageHandler(StorageHandler):
    """Sube archivos a un servidor FTP."""

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
        try:
            ftp = self._get_client()
            with open(temp_path, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)

            base_dir = settings.FTP_DIR.rstrip("/")
            saved_path = f"ftp://{settings.FTP_HOST}:{settings.FTP_PORT}{base_dir}/{filename}"
            logger.info("FTPStorage: '%s' → %s", filename, saved_path)
            return saved_path
        finally:
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass
