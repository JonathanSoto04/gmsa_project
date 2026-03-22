"""
Archivo : routers/history.py
Descripción:
    Router de FastAPI que expone los endpoints para consultar y administrar
    el historial de cargas de archivos.

    El historial se persiste en disco como un archivo JSON gestionado por
    la capa de servicios. Este router se limita a exponer las operaciones
    de lectura y borrado sin acceder directamente al sistema de archivos.

Responsabilidades:
    - Exponer ``GET /history``    — devuelve todos los registros, del más reciente al más antiguo.
    - Exponer ``DELETE /history`` — elimina todos los registros del historial.

Arquitectura:
    Forma parte de la capa de routers. Depende de:
        · app.schemas.HistoryResponse          — como modelo de respuesta.
        · app.services.history_service         — para las operaciones de I/O del historial.
"""

from fastapi import APIRouter

from app.schemas import HistoryResponse
from app.services.history_service import clear_history, load_history

# Instancia del router con prefijo de ruta y etiqueta para la documentación.
router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=HistoryResponse, summary="Historial de cargas")
def get_history() -> HistoryResponse:
    """
    Recupera todos los registros del historial de cargas almacenados en disco.

    Los registros se devuelven en orden cronológico inverso (el más reciente
    aparece primero) para facilitar la visualización en el dashboard.

    Retorna:
        ``HistoryResponse`` con el total de registros y la lista completa
        ordenada de más reciente a más antiguo.
    """
    # La lista se invierte en este nivel para no acoplar el orden al servicio,
    # permitiendo que otros consumidores obtengan el orden original si lo necesitan.
    items = load_history()[::-1]
    return HistoryResponse(total=len(items), items=items)


@router.delete("", summary="Limpiar historial")
def delete_history() -> dict:
    """
    Elimina permanentemente todos los registros del historial almacenados en disco.

    Esta operación es irreversible. El archivo de historial queda vacío
    tras la llamada. No se requiere confirmación adicional desde este endpoint;
    la confirmación debe gestionarse en el lado del cliente.

    Retorna:
        Diccionario con ``success: True`` y un mensaje informativo.
    """
    clear_history()
    return {"success": True, "message": "Historial eliminado correctamente."}
