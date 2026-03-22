"""
routers/history.py
------------------
Endpoints for reading and clearing the upload history.
"""

from fastapi import APIRouter

from app.schemas import HistoryResponse
from app.services.history_service import clear_history, load_history

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=HistoryResponse, summary="Historial de cargas")
def get_history() -> HistoryResponse:
    """Returns all upload records sorted newest-first."""
    items = load_history()[::-1]
    return HistoryResponse(total=len(items), items=items)


@router.delete("", summary="Limpiar historial")
def delete_history() -> dict:
    """Deletes all history records from disk."""
    clear_history()
    return {"success": True, "message": "Historial eliminado correctamente."}
