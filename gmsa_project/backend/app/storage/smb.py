"""
storage/smb.py
--------------
StorageHandler para SMB (Samba / Windows Share / TrueNAS).

Lee credenciales desde settings (que a su vez las carga del .env).
Registra la sesión SMB antes de cada operación y sube el archivo
usando smbclient con escritura binaria directa.
"""

from __future__ import annotations

import logging
from pathlib import Path

import smbclient
import smbprotocol.connection

from app.config import settings
from app.storage.base import StorageHandler

logger = logging.getLogger(__name__)


class SMBStorageHandler(StorageHandler):
    """Sube archivos a un share SMB."""

    def _register_session(self) -> None:
        smbprotocol.connection.MAX_PAYLOAD_SIZE = 1048576
        smbclient.ClientConfig(
            username=settings.SMB_USER,
            password=settings.SMB_PASS,
            require_secure_negotiate=False,
        )
        smbclient.reset_connection_cache()
        smbclient.register_session(
            settings.SMB_HOST,
            username=settings.SMB_USER,
            password=settings.SMB_PASS,
            encrypt=False,
            require_signing=False,
        )

    def save(self, temp_path: Path, filename: str) -> str:
        self._register_session()

        remote_path = f"//{settings.SMB_HOST}/{settings.SMB_SHARE}/{filename}"
        contents = temp_path.read_bytes()

        with smbclient.open_file(remote_path, mode="wb") as f:
            f.write(contents)

        saved_path = f"//{settings.SMB_HOST}/{settings.SMB_SHARE}/{filename}"
        logger.info("SMBStorage: '%s' → %s", filename, saved_path)
        return saved_path
