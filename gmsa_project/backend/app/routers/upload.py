"""
Archivo : routers/upload.py
Descripción:
    Router de FastAPI responsable del endpoint de carga de archivos.

    Este módulo actúa como capa de presentación HTTP: valida los parámetros
    de entrada a nivel de protocolo web y delega toda la lógica de negocio
    al servicio ``upload_service``. El router no realiza operaciones de
    almacenamiento ni de historial directamente.

Responsabilidades:
    - Exponer el endpoint ``POST /upload``.
    - Validar que el protocolo recibido sea uno de los admitidos.
    - Invocar ``process_upload()`` y retornar la respuesta estructurada.

Arquitectura:
    Forma parte de la capa de routers. Depende de:
        · app.config.settings         — para verificar protocolos válidos.
        · app.schemas.UploadResponse  — como modelo de respuesta.
        · app.services.upload_service — para ejecutar el flujo de carga.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.schemas import UploadResponse
from app.services.upload_service import process_upload

# Instancia del router con prefijo de ruta y etiqueta para la documentación.
router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse, summary="Subir archivo")
async def upload_file(
    protocol: str = Form(..., description="Protocolo destino (nfs, ftp, sftp, s3, smb)."),
    username: str = Form("", description="Usuario — requerido en integraciones reales."),
    password: str = Form("", description="Contraseña — almacenada para futura integración."),
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    Recibe una carga multipart/form-data y enruta el archivo al manejador
    de almacenamiento correspondiente al protocolo seleccionado.

    Parámetros de formulario:
        protocol : Protocolo de almacenamiento destino. Debe ser uno de los
                   valores registrados en ``settings.SUPPORTED_PROTOCOLS``.
        username : Nombre de usuario para la sesión de almacenamiento.
                   Opcional en modo simulación, requerido con protocolos reales.
        password : Contraseña del usuario. Se acepta en la firma del endpoint
                   para mantener compatibilidad futura con integraciones reales
                   sin necesidad de cambiar la API; no se utiliza en simulación.
        file     : Archivo binario a subir, enviado como ``multipart/form-data``.

    Retorna:
        ``UploadResponse`` con el resultado de la operación y el registro
        persistido en el historial.

    Lanza:
        HTTPException 422 — si el protocolo no está soportado.
        HTTPException 422 — si la extensión o el tamaño del archivo no son válidos
                            (propagado desde ``process_upload``).
        HTTPException 500 — si ocurre un fallo inesperado en la capa de almacenamiento.
    """
    # Normalización del protocolo: se elimina espacios y se convierte a minúsculas
    # para garantizar comparaciones consistentes contra el registro de handlers.
    protocol = protocol.lower().strip()

    # Validación anticipada del protocolo antes de procesar el archivo,
    # evitando operaciones innecesarias con entradas inválidas.
    if protocol not in settings.SUPPORTED_PROTOCOLS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Protocolo '{protocol}' no válido. "
                f"Opciones: {', '.join(sorted(settings.SUPPORTED_PROTOCOLS))}."
            ),
        )

    # Delegación al servicio de carga; aquí se ejecuta el pipeline completo:
    # validación de extensión → escritura temporal → almacenamiento → historial.
    record = await process_upload(file=file, protocol=protocol, username=username)

    return UploadResponse(
        success=True,
        message=f"Archivo subido correctamente vía {protocol.upper()}.",
        record=record,
    )
