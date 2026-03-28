"""Router para listar y eliminar archivos locales por protocolo."""

from fastapi import APIRouter, HTTPException, Query

from app.schemas import DeleteFileRequest, DeleteFileResponse, FilesListResponse
from app.services.files_service import delete_file, list_files
from app.storage.base import (
    StorageAuthenticationError,
    StorageConfigurationError,
    StorageError,
    StoragePathError,
    StoragePermissionError,
)

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("", response_model=FilesListResponse, summary="Listar archivos almacenados")
def get_files(
    protocol: str | None = Query(
        default=None,
        description="Filtra por protocolo. Si se omite, lista todos los archivos.",
    )
) -> FilesListResponse:
    try:
        result = list_files(protocol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except StorageAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (StoragePathError, StorageConfigurationError, StorageError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return FilesListResponse(
        total=len(result["items"]),
        items=result["items"],
        warnings=result["warnings"],
    )


@router.delete("", response_model=DeleteFileResponse, summary="Eliminar archivo almacenado")
def remove_file(payload: DeleteFileRequest) -> DeleteFileResponse:
    try:
        result = delete_file(protocol=payload.protocol, filename=payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    remote_deleted = result["remote_deleted"]
    warning = result["warning"]
    return DeleteFileResponse(
        success=True,
        message=(
            f"Archivo '{payload.name}' eliminado del protocolo {payload.protocol.upper()} "
            "en el destino remoto y en la copia local."
            if remote_deleted
            else
            f"Archivo '{payload.name}' eliminado de la copia local del protocolo "
            f"{payload.protocol.upper()}, pero el borrado remoto no se completo."
        ),
        deleted=result["deleted"],
        remote_deleted=remote_deleted,
        local_deleted=result["local_deleted"],
        warning=warning,
    )
