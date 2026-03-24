"""
Archivo : routers/upload.py
Descripcion:
    Endpoint HTTP para recibir archivos y delegar la logica de carga al servicio.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.schemas import UploadResponse
from app.services.upload_service import process_upload

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse, summary="Subir archivo")
async def upload_file(
    protocol: str = Form(..., description="Protocolo destino (nfs, ftp, s3, smb)."),
    username: str = Form("", description="Usuario para la sesion remota."),
    password: str = Form("", description="Contrasena para la sesion remota."),
    file: UploadFile = File(...),
) -> UploadResponse:
    """Recibe un multipart/form-data y lo enruta al handler correspondiente."""
    protocol = protocol.lower().strip()

    if protocol not in settings.SUPPORTED_PROTOCOLS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Protocolo '{protocol}' no valido. "
                f"Opciones: {', '.join(sorted(settings.SUPPORTED_PROTOCOLS))}."
            ),
        )

    if bool(username.strip()) != bool(password):
        raise HTTPException(
            status_code=422,
            detail="Debes enviar username y password juntos, o dejar ambos vacios.",
        )

    record = await process_upload(
        file=file,
        protocol=protocol,
        username=username,
        password=password,
    )

    return UploadResponse(
        success=True,
        message=f"Archivo subido correctamente via {protocol.upper()}.",
        record=record,
    )
