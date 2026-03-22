"""
services/history_service.py
----------------------------
All history read/write operations in one place.

Keeping I/O logic here means routers and upload_service never touch
the filesystem directly — they call these functions instead.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _ensure_storage() -> None:
    """Creates the data directory and an empty history file if missing."""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.HISTORY_FILE.exists():
        settings.HISTORY_FILE.write_text("[]", encoding="utf-8")


def load_history() -> list[dict]:
    """Reads and returns all history records from disk."""
    _ensure_storage()
    try:
        with open(settings.HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read history file: %s", exc)
        return []


def save_history(records: list[dict]) -> None:
    """Writes the full records list to disk, overwriting the current file."""
    _ensure_storage()
    with open(settings.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def append_record(record: dict) -> None:
    """Appends a single record to the persisted history."""
    records = load_history()
    records.append(record)
    save_history(records)


def clear_history() -> None:
    """Removes all history records."""
    save_history([])


# ---------------------------------------------------------------------------
# Record factory
# ---------------------------------------------------------------------------

def build_record(
    *,
    filename: str,
    protocol: str,
    username: str,
    size_kb: float,
    status: str,
    saved_path: str,
) -> dict:
    """
    Builds a uniform history record dict.
    Using keyword-only args prevents positional mistakes.
    """
    return {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "protocol": protocol.upper(),
        "username": username or "No especificado",
        "size_kb": round(size_kb, 2),
        "status": status,
        "saved_path": saved_path,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
