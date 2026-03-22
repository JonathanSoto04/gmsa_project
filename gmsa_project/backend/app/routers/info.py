"""
routers/info.py
---------------
General-purpose endpoints: health check and frontend configuration.
"""

from fastapi import APIRouter

from app.config import settings
from app.schemas import ConfigResponse

router = APIRouter(tags=["Info"])


@router.get("/", summary="Health check")
def root() -> dict:
    """Quick liveness check — confirms the API is reachable."""
    return {
        "status": "online",
        "api": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/config", response_model=ConfigResponse, summary="Configuración pública")
def get_config() -> ConfigResponse:
    """
    Returns settings consumed by the frontend to drive UI behaviour:
    max file size, allowed extensions, and supported protocols.
    """
    return ConfigResponse(
        project_name=settings.PROJECT_NAME,
        max_file_size_mb=settings.MAX_FILE_SIZE_MB,
        allowed_extensions=sorted(settings.ALLOWED_EXTENSIONS),
        supported_protocols=sorted(settings.SUPPORTED_PROTOCOLS),
    )
