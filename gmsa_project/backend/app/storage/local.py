"""Manejador de almacenamiento local de apoyo."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.config import settings
from app.storage.base import StorageCredentials, StorageHandler

logger = logging.getLogger(__name__)


class LocalStorageHandler(StorageHandler):
    """Copia y elimina archivos en un subdirectorio local por protocolo."""

    def __init__(self, subfolder: str) -> None:
        self._dest: Path = settings.UPLOAD_DIR / subfolder
        self._dest.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        destination = self._dest / Path(filename).name
        shutil.copy(temp_path, destination)
        logger.info("LocalStorage save OK '%s' -> %s", filename, destination)
        return str(destination.resolve())

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        destination = self._dest / Path(filename).name
        destination.unlink(missing_ok=True)
        logger.info("LocalStorage delete OK '%s' -> %s", filename, destination)
