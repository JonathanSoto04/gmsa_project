"""
Archivo : routers/info.py
Descripción:
    Router de FastAPI con endpoints de propósito general: verificación de
    disponibilidad (health check) y configuración pública de la API.

    Estos endpoints no requieren autenticación ni parámetros adicionales,
    y son utilizados principalmente por el frontend al inicializarse para
    conocer el estado del backend y obtener los parámetros de configuración
    que definen el comportamiento de la interfaz.

Responsabilidades:
    - Exponer ``GET /``       — health check que confirma que la API está en línea.
    - Exponer ``GET /config`` — devuelve la configuración pública consumida por el frontend.

Arquitectura:
    Forma parte de la capa de routers. Depende de:
        · app.config.settings          — para leer los valores de configuración.
        · app.schemas.ConfigResponse   — como modelo de respuesta estructurada.
"""

from fastapi import APIRouter

from app.config import settings
from app.schemas import ConfigResponse

# Router sin prefijo; los endpoints se montan en la raíz de la API.
router = APIRouter(tags=["Info"])


@router.get("/", summary="Health check")
def root() -> dict:
    """
    Verificación de disponibilidad de la API (health check).

    Permite al frontend y a herramientas de monitoreo confirmar que el
    servidor está en línea y respondiendo correctamente antes de realizar
    operaciones más complejas.

    Retorna:
        Diccionario con el estado del servicio, el nombre del proyecto
        y la versión actual de la API.
    """
    return {
        "status": "online",
        "api": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/config", response_model=ConfigResponse, summary="Configuración pública")
def get_config() -> ConfigResponse:
    """
    Expone la configuración pública de la API para ser consumida por el frontend.

    El frontend utiliza estos valores para:
        - Limitar el tamaño de los archivos seleccionables antes de enviarlos.
        - Mostrar las extensiones permitidas en la interfaz de carga.
        - Renderizar dinámicamente los botones de selección de protocolo.

    De esta forma, cualquier cambio en la configuración del backend se
    refleja automáticamente en el frontend sin necesidad de modificar el código
    del cliente.

    Retorna:
        ``ConfigResponse`` con el nombre del proyecto, tamaño máximo permitido,
        extensiones aceptadas y protocolos disponibles, todos ordenados
        alfabéticamente para presentación consistente.
    """
    return ConfigResponse(
        project_name=settings.PROJECT_NAME,
        max_file_size_mb=settings.MAX_FILE_SIZE_MB,
        allowed_extensions=sorted(settings.ALLOWED_EXTENSIONS),
        supported_protocols=sorted(settings.SUPPORTED_PROTOCOLS),
    )
