"""
storage/registry.py
-------------------
Maps protocol names to their storage handler instances.

This is THE single place to swap in a real protocol implementation.
Everything else in the application is unaffected by changes here.

To add or replace a handler:
  1. Create a new StorageHandler subclass (e.g. storage/s3.py).
  2. Instantiate it below and assign it to the relevant protocol key.
  3. Done — no changes needed elsewhere.
"""

from __future__ import annotations

from app.storage.base import StorageHandler
from app.storage.local import LocalStorageHandler

# ---------------------------------------------------------------------------
# Protocol → handler mapping
#
# FTP and SFTP share the same local folder in simulation mode.
# When integrating real protocols, they can each get an independent handler.
# ---------------------------------------------------------------------------
_REGISTRY: dict[str, StorageHandler] = {
    "nfs":  LocalStorageHandler("nfs"),
    "ftp":  LocalStorageHandler("ftp"),
    "sftp": LocalStorageHandler("ftp"),   # shared folder — replace independently
    "s3":   LocalStorageHandler("s3"),
    "smb":  LocalStorageHandler("smb"),
}


def get_handler(protocol: str) -> StorageHandler:
    """Returns the storage handler registered for `protocol`."""
    handler = _REGISTRY.get(protocol.lower())
    if handler is None:
        raise ValueError(f"No storage handler registered for protocol: '{protocol}'")
    return handler
