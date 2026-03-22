"""
storage/base.py
---------------
Abstract base class for all storage backends.

To integrate a real protocol, subclass `StorageHandler`, implement `save()`,
and register the new handler in `storage/registry.py`.

Example — adding a real FTP handler:

    # storage/ftp.py
    from ftplib import FTP
    from app.storage.base import StorageHandler

    class FTPStorageHandler(StorageHandler):
        def __init__(self, host: str, user: str, password: str) -> None:
            self._host = host
            self._user = user
            self._password = password

        def save(self, temp_path: Path, filename: str) -> str:
            with FTP(self._host) as ftp:
                ftp.login(self._user, self._password)
                with open(temp_path, "rb") as f:
                    ftp.storbinary(f"STOR {filename}", f)
            return f"ftp://{self._host}/{filename}"

    # storage/registry.py  (add this line)
    "ftp": FTPStorageHandler(host="...", user="...", password="..."),
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageHandler(ABC):
    """Contract that every storage backend must satisfy."""

    @abstractmethod
    def save(self, temp_path: Path, filename: str) -> str:
        """
        Persist the file located at `temp_path`.

        Args:
            temp_path: Path to the temporary file written by the upload service.
            filename:  Original filename provided by the client.

        Returns:
            A string identifying where the file was stored
            (absolute path, URL, bucket key, etc.).
        """
        ...
