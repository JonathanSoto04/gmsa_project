"""Servicios para listar, copiar y eliminar archivos por protocolo."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.storage.base import StorageError
from app.storage.registry import get_handler

logger = logging.getLogger(__name__)


def list_files(protocol: str | None = None) -> dict:
    """Lista archivos remotos por protocolo y agrega advertencias por fallos parciales."""
    items: list[dict] = []
    warnings: list[str] = []
    protocols = _resolve_protocols(protocol)

    for protocol_name in protocols:
        try:
            handler = get_handler(protocol_name)
            protocol_items = handler.list_files()
            items.extend(protocol_items)
        except StorageError as exc:
            if protocol:
                raise
            warnings.append(f"{protocol_name.upper()}: {exc}")
            logger.warning("Remote list failed for %s: %s", protocol_name.upper(), exc)

    items.sort(key=lambda item: item["modified_at"], reverse=True)
    return {"items": items, "warnings": warnings}


def delete_file(*, protocol: str, filename: str) -> dict:
    """Elimina el archivo remoto y limpia la copia local si existe."""
    safe_protocol = _validate_protocol(protocol)
    safe_name = _validate_filename(filename)

    remote_metadata = _find_remote_file(protocol=safe_protocol, filename=safe_name)
    local_path = _resolve_file_path(protocol=safe_protocol, filename=safe_name)
    local_exists = local_path.exists() and local_path.is_file()

    if remote_metadata is None and not local_exists:
        raise FileNotFoundError(
            f"El archivo '{safe_name}' no existe en el protocolo '{safe_protocol}'."
        )

    deleted_item = remote_metadata or _build_local_item(protocol=safe_protocol, file_path=local_path)
    remote_deleted = True
    warning = None

    try:
        _delete_remote_file(protocol=safe_protocol, filename=safe_name)
    except StorageError as exc:
        remote_deleted = False
        warning = str(exc)
        logger.warning(
            "Remote delete failed for '%s' via %s: %s",
            safe_name,
            safe_protocol.upper(),
            exc,
        )

    if local_exists:
        local_path.unlink()

    return {
        "deleted": deleted_item,
        "remote_deleted": remote_deleted,
        "local_deleted": local_exists,
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


def _build_local_item(*, protocol: str, file_path: Path) -> dict:
    timestamp = _format_timestamp(datetime.now().timestamp())
    if file_path.exists() and file_path.is_file():
        stat = file_path.stat()
        timestamp = _format_timestamp(stat.st_mtime)
        size = int(stat.st_size)
    else:
        size = 0

    return {
        "name": file_path.name,
        "protocol": protocol,
        "size": size,
        "path": f"{protocol}://desconocido/{file_path.name}",
        "created_at": timestamp,
        "modified_at": timestamp,
    }


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _delete_remote_file(*, protocol: str, filename: str) -> None:
    handler = get_handler(protocol)
    handler.delete(filename)


def _find_remote_file(*, protocol: str, filename: str) -> dict | None:
    handler = get_handler(protocol)
    for item in handler.list_files():
        if item["name"] == filename:
            return item
    return None
