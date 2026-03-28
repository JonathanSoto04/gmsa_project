"""Servicios para listar, copiar y eliminar archivos locales por protocolo."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.storage.base import StorageError
from app.storage.registry import get_handler

logger = logging.getLogger(__name__)


def list_files(protocol: str | None = None) -> list[dict]:
    """Lista archivos del directorio local uploads/<protocolo>."""
    items: list[dict] = []

    for protocol_name in _resolve_protocols(protocol):
        directory = settings.get_protocol_upload_dir(protocol_name)

        for candidate in directory.iterdir():
            if not candidate.is_file():
                continue

            stat = candidate.stat()
            items.append(
                {
                    "name": candidate.name,
                    "protocol": protocol_name,
                    "size": stat.st_size,
                    "path": candidate.relative_to(settings.UPLOAD_DIR).as_posix(),
                    "created_at": _format_timestamp(stat.st_ctime),
                    "modified_at": _format_timestamp(stat.st_mtime),
                    "_sort_ts": stat.st_mtime,
                }
            )

    items.sort(key=lambda item: item["_sort_ts"], reverse=True)
    for item in items:
        item.pop("_sort_ts", None)

    return items


def delete_file(*, protocol: str, filename: str) -> dict:
    """Elimina la copia local y reporta si el borrado remoto tambien se completo."""
    safe_protocol = _validate_protocol(protocol)
    file_path = _resolve_file_path(protocol=safe_protocol, filename=filename)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(
            f"El archivo '{filename}' no existe en el protocolo '{safe_protocol}'."
        )

    metadata = _build_item(protocol=safe_protocol, file_path=file_path)
    remote_deleted = True
    warning = None

    try:
        _delete_remote_file(protocol=safe_protocol, filename=file_path.name)
    except StorageError as exc:
        remote_deleted = False
        warning = str(exc)
        logger.warning(
            "Remote delete failed for '%s' via %s: %s",
            file_path.name,
            safe_protocol.upper(),
            exc,
        )

    file_path.unlink()
    return {
        "deleted": metadata,
        "remote_deleted": remote_deleted,
        "local_deleted": True,
        "warning": warning,
    }


def store_local_file_copy(*, protocol: str, temp_path: Path, filename: str | None) -> Path:
    """Guarda una copia espejo local del archivo subido."""
    file_path = _resolve_file_path(protocol=protocol, filename=filename)
    shutil.copy2(temp_path, file_path)
    return file_path


def delete_local_file_copy(*, protocol: str, filename: str | None) -> None:
    """Elimina la copia local si existe."""
    if not filename:
        return

    try:
        file_path = _resolve_file_path(protocol=protocol, filename=filename)
    except ValueError:
        return

    file_path.unlink(missing_ok=True)


def _resolve_protocols(protocol: str | None) -> list[str]:
    if protocol is None or not protocol.strip():
        return sorted(settings.SUPPORTED_PROTOCOLS)
    return [_validate_protocol(protocol)]


def _validate_protocol(protocol: str) -> str:
    normalized = protocol.lower().strip()
    if normalized not in settings.SUPPORTED_PROTOCOLS:
        raise ValueError(
            f"Protocolo '{protocol}' no valido. "
            f"Opciones: {', '.join(sorted(settings.SUPPORTED_PROTOCOLS))}."
        )
    return normalized


def _validate_filename(filename: str | None) -> str:
    cleaned = (filename or "").strip()
    safe_name = Path(cleaned).name

    if not cleaned:
        raise ValueError("Debes indicar un nombre de archivo valido.")
    if safe_name != cleaned or safe_name in {".", ".."}:
        raise ValueError("Nombre de archivo invalido. No se permiten rutas embebidas ni '..'.")
    if "/" in safe_name or "\\" in safe_name:
        raise ValueError("Nombre de archivo invalido. No se permiten separadores de ruta.")

    return safe_name


def _resolve_file_path(*, protocol: str, filename: str | None) -> Path:
    safe_protocol = _validate_protocol(protocol)
    safe_name = _validate_filename(filename)

    directory = settings.get_protocol_upload_dir(safe_protocol).resolve()
    file_path = (directory / safe_name).resolve()

    try:
        file_path.relative_to(directory)
    except ValueError as exc:
        raise ValueError("Ruta de archivo invalida.") from exc

    return file_path


def _build_item(*, protocol: str, file_path: Path) -> dict:
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "protocol": protocol,
        "size": stat.st_size,
        "path": file_path.relative_to(settings.UPLOAD_DIR.resolve()).as_posix(),
        "created_at": _format_timestamp(stat.st_ctime),
        "modified_at": _format_timestamp(stat.st_mtime),
    }


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _delete_remote_file(*, protocol: str, filename: str) -> None:
    handler = get_handler(protocol)
    handler.delete(filename)
