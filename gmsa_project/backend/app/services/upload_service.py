"""Servicio principal de carga de archivos."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.files_service import delete_local_file_copy, store_local_file_copy
from app.services.history_service import append_record, build_record
from app.storage.base import (
    StorageAuthenticationError,
    StorageConfigurationError,
    StorageCredentials,
    StorageError,
    StoragePathError,
    StoragePermissionError,
)
from app.storage.registry import get_handler

logger = logging.getLogger(__name__)


async def process_upload(
    *,
    file: UploadFile,
    protocol: str,
    username: str,
    password: str,
) -> dict:
    """Ejecuta el pipeline completo de carga de un archivo."""
    _validate_extension(file.filename)
    temp_path, size_bytes = await _stream_to_temp(file)
    credentials = StorageCredentials(username=username.strip(), password=password)
    local_copy_path: Path | None = None

    try:
        local_copy_path = store_local_file_copy(
            protocol=protocol,
            temp_path=temp_path,
            filename=file.filename,
        )

        handler = get_handler(protocol)
        saved_path = handler.save(temp_path, file.filename, credentials)

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
            "Upload OK - '%s' via %s (%.1f KB) by '%s'",
            file.filename,
            protocol.upper(),
            size_bytes / 1024,
            username or "anon",
        )
        return record

    except HTTPException:
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        raise
    except StorageAuthenticationError as exc:
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(status_code=401, detail=str(exc))
    except StoragePermissionError as exc:
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(status_code=403, detail=str(exc))
    except (StoragePathError, StorageConfigurationError) as exc:
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(status_code=500, detail=str(exc))
    except StorageError as exc:
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(status_code=500, detail=f"Error de almacenamiento: {exc}")
    except Exception as exc:
        logger.exception("Storage failure for '%s' via %s", file.filename, protocol.upper())
        _rollback_local_copy(protocol=protocol, filename=file.filename, local_copy_path=local_copy_path)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el archivo via {protocol.upper()}: {exc}",
        )
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_extension(filename: str | None) -> None:
    """Verifica que la extension del archivo este permitida."""
    if not filename:
        raise HTTPException(status_code=422, detail="El archivo debe incluir un nombre valido.")

    ext = Path(filename).suffix.lower()
    if not ext or ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Extension '{ext or 'ninguna'}' no permitida. "
                f"Tipos aceptados: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            ),
        )


async def _stream_to_temp(file: UploadFile) -> tuple[Path, int]:
    """Escribe el stream del request en un archivo temporal unico."""
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "upload.bin").name
    temp_path = settings.TEMP_DIR / f"{uuid.uuid4()}_{safe_name}"
    size_bytes = 0

    try:
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > settings.MAX_FILE_SIZE_BYTES:
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=422,
                        detail=f"El archivo supera el limite de {settings.MAX_FILE_SIZE_MB} MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error de escritura temporal: {exc}")

    return temp_path, size_bytes


def _rollback_local_copy(
    *, protocol: str, filename: str | None, local_copy_path: Path | None
) -> None:
    if local_copy_path is None or not filename:
        return
    delete_local_file_copy(protocol=protocol, filename=filename)


def _record_error(filename: str, protocol: str, username: str, size_bytes: int) -> None:
    """Persiste un registro de fallo en el historial."""
    record = build_record(
        filename=filename,
        protocol=protocol,
        username=username,
        size_kb=size_bytes / 1024 if size_bytes else 0,
        status="Error",
        saved_path="-",
    )
    append_record(record)
