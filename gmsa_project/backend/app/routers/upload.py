"""
routers/upload.py
-----------------
File upload endpoint.

The router is intentionally thin: it validates HTTP-level inputs,
delegates all business logic to upload_service, and shapes the response.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.schemas import UploadResponse
from app.services.upload_service import process_upload

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse, summary="Subir archivo")
async def upload_file(
    protocol: str = Form(..., description="Protocolo destino (nfs, ftp, sftp, s3, smb)."),
    username: str = Form("", description="Usuario — requerido en integraciones reales."),
    password: str = Form("", description="Contraseña — almacenada para futura integración."),
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Receives a multipart upload and routes the file through the selected
    protocol handler. `password` is accepted but not acted on in simulation
    mode — it is available for real protocol integrations without API changes.
    """
    protocol = protocol.lower().strip()

    if protocol not in settings.SUPPORTED_PROTOCOLS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Protocolo '{protocol}' no válido. "
                f"Opciones: {', '.join(sorted(settings.SUPPORTED_PROTOCOLS))}."
            ),
        )

    record = await process_upload(file=file, protocol=protocol, username=username)

    return UploadResponse(
        success=True,
        message=f"Archivo subido correctamente vía {protocol.upper()}.",
        record=record,
    )
