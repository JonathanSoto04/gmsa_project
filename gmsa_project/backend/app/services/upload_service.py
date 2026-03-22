"""
services/upload_service.py
---------------------------
Orchestrates the complete file upload flow.

Routers are kept thin — they validate HTTP-level inputs, then delegate
all business logic to `process_upload()` here.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.history_service import append_record, build_record
from app.storage.registry import get_handler

logger = logging.getLogger(__name__)


async def process_upload(
    *,
    file: UploadFile,
    protocol: str,
    username: str,
) -> dict:
    """
    Runs the upload pipeline:
      1. Validate file extension.
      2. Stream to a temporary file, enforcing the size limit.
      3. Hand off to the protocol storage handler.
      4. Record the result in history.
      5. Clean up the temporary file.

    Only genuine storage failures are recorded in history.
    Validation errors (bad extension, size exceeded) are raised immediately
    and never written to the history log.

    Returns:
        The history record dict on success.

    Raises:
        HTTPException 422 — validation failure (extension, size).
        HTTPException 500 — unexpected storage error.
    """
    _validate_extension(file.filename)

    temp_path, size_bytes = await _stream_to_temp(file)

    try:
        handler = get_handler(protocol)
        saved_path = handler.save(temp_path, file.filename)

        record = build_record(
            filename=file.filename,
            protocol=protocol,
            username=username,
            size_kb=size_bytes / 1024,
            status="Éxito",
            saved_path=saved_path,
        )
        append_record(record)

        logger.info(
            "Upload OK — '%s' via %s (%.1f KB) by '%s'",
            file.filename,
            protocol.upper(),
            size_bytes / 1024,
            username or "anon",
        )
        return record

    except HTTPException:
        raise

    except Exception as exc:
        logger.error("Storage failure for '%s': %s", file.filename, exc)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el archivo via {protocol.upper()}: {exc}",
        )

    finally:
        temp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if not ext or ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Extensión '{ext or 'ninguna'}' no permitida. "
                f"Tipos aceptados: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            ),
        )


async def _stream_to_temp(file: UploadFile) -> tuple[Path, int]:
    """Writes the upload stream to a unique temporary file, chunk by chunk."""
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = settings.TEMP_DIR / f"{uuid.uuid4()}_{file.filename}"
    size_bytes = 0

    try:
        with open(temp_path, "wb") as buf:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                size_bytes += len(chunk)
                if size_bytes > settings.MAX_FILE_SIZE_BYTES:
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=422,
                        detail=f"El archivo supera el límite de {settings.MAX_FILE_SIZE_MB} MB.",
                    )
                buf.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error de escritura temporal: {exc}")

    return temp_path, size_bytes


def _record_error(
    filename: str, protocol: str, username: str, size_bytes: int
) -> None:
    """Persists a failed upload attempt to history."""
    record = build_record(
        filename=filename,
        protocol=protocol,
        username=username,
        size_kb=size_bytes / 1024 if size_bytes else 0,
        status="Error",
        saved_path="-",
    )
    append_record(record)
