"""
storage/local.py
----------------
Simulation storage handler: copies files to a local subdirectory.

Each protocol gets its own subfolder under `settings.UPLOAD_DIR`.
When a real protocol integration is ready, replace (or stop registering)
this handler for that protocol in `storage/registry.py`.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.config import settings
from app.storage.base import StorageHandler

logger = logging.getLogger(__name__)


class LocalStorageHandler(StorageHandler):
    """
    Stores files in a local subdirectory, simulating a remote target.

    Args:
        subfolder: Name of the directory under `settings.UPLOAD_DIR`
                   that this handler writes to (e.g. "nfs", "s3").
    """

    def __init__(self, subfolder: str) -> None:
        self._dest: Path = settings.UPLOAD_DIR / subfolder
        self._dest.mkdir(parents=True, exist_ok=True)

    def save(self, temp_path: Path, filename: str) -> str:
        destination = self._dest / filename
        shutil.copy(temp_path, destination)
        logger.info("LocalStorage: '%s' → %s", filename, destination)
        return str(destination.resolve())
