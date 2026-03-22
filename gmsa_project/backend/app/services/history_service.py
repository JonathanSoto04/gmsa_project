"""
Archivo : services/history_service.py
Descripción:
    Servicio encargado de todas las operaciones de lectura y escritura
    sobre el historial de cargas de archivos.

    El historial se persiste en un archivo JSON local ubicado en la ruta
    definida por ``settings.HISTORY_FILE``. Al centralizar las operaciones
    de I/O en este módulo, los routers y el servicio de carga no acceden
    directamente al sistema de archivos, lo que facilita pruebas y
    posibles migraciones a otras fuentes de datos en el futuro.

Responsabilidades:
    - Crear el directorio y el archivo de historial si no existen.
    - Leer, guardar, añadir y borrar registros del historial.
    - Construir registros con una estructura uniforme y validada.

Arquitectura:
    Forma parte de la capa de servicios. Depende de:
        · app.config.settings — para las rutas del sistema de archivos.

    Es utilizado por:
        · app.services.upload_service — para persistir resultados de carga.
        · app.routers.history         — para exponer y administrar el historial.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from app.config import settings

# Logger con el nombre del módulo para facilitar el filtrado en los logs.
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funciones de acceso al almacenamiento
# ---------------------------------------------------------------------------

def _ensure_storage() -> None:
    """
    Garantiza que el directorio de datos y el archivo de historial existan.

    Si el directorio ``settings.DATA_DIR`` no existe, lo crea junto con
    todos los directorios intermedios necesarios. Si el archivo de historial
    no existe, lo inicializa con una lista JSON vacía ``[]``.

    Esta función debe llamarse al inicio de cualquier operación de I/O
    para evitar errores por rutas inexistentes.
    """
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.HISTORY_FILE.exists():
        settings.HISTORY_FILE.write_text("[]", encoding="utf-8")


def load_history() -> list[dict]:
    """
    Lee y retorna todos los registros del historial almacenados en disco.

    En caso de error de lectura o de formato JSON inválido, se registra
    el incidente en el log y se retorna una lista vacía para no interrumpir
    el flujo de la aplicación.

    Retorna:
        Lista de diccionarios; cada elemento representa una carga registrada.
        Retorna ``[]`` si el archivo está vacío, no existe o tiene formato inválido.
    """
    _ensure_storage()
    try:
        with open(settings.HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Error al leer el archivo de historial: %s", exc)
        return []


def save_history(records: list[dict]) -> None:
    """
    Escribe la lista completa de registros en el archivo de historial,
    sobreescribiendo el contenido anterior.

    Parámetros:
        records : Lista de diccionarios que representa el historial completo
                  a persistir. Puede ser una lista vacía para limpiar el historial.
    """
    _ensure_storage()
    with open(settings.HISTORY_FILE, "w", encoding="utf-8") as f:
        # ``indent=2`` mejora la legibilidad del JSON al inspeccionarlo manualmente.
        # ``ensure_ascii=False`` preserva caracteres especiales como tildes y ñ.
        json.dump(records, f, indent=2, ensure_ascii=False)


def append_record(record: dict) -> None:
    """
    Añade un único registro al final del historial persistido en disco.

    La operación es de lectura-modificación-escritura: se carga el historial
    completo, se agrega el nuevo registro y se guarda de nuevo. Para sistemas
    con alta concurrencia se recomienda implementar un mecanismo de bloqueo.

    Parámetros:
        record : Diccionario con la estructura de un ``UploadRecord`` a persistir.
    """
    records = load_history()
    records.append(record)
    save_history(records)


def clear_history() -> None:
    """
    Elimina todos los registros del historial reemplazando el contenido
    del archivo con una lista vacía.

    Esta operación es irreversible.
    """
    save_history([])


# ---------------------------------------------------------------------------
# Fábrica de registros
# ---------------------------------------------------------------------------

def build_record(
    *,
    filename: str,
    protocol: str,
    username: str,
    size_kb: float,
    status: str,
    saved_path: str,
) -> dict:
    """
    Construye un diccionario de registro de historial con estructura uniforme.

    El uso de argumentos exclusivamente por nombre (``*``) previene errores
    de posicionamiento al invocar la función con múltiples parámetros del
    mismo tipo.

    Parámetros (solo por nombre):
        filename   : Nombre original del archivo.
        protocol   : Protocolo utilizado; se almacena en mayúsculas.
        username   : Nombre del usuario; si está vacío, se asigna ``"No especificado"``.
        size_kb    : Tamaño del archivo en kilobytes.
        status     : Resultado de la operación: ``"Éxito"`` o ``"Error"``.
        saved_path : Ruta o identificador donde quedó almacenado el archivo.
                     Se usa ``"-"`` cuando el almacenamiento falló.

    Retorna:
        Diccionario que cumple la estructura definida en ``schemas.UploadRecord``.
    """
    return {
        "id": str(uuid.uuid4()),                              # identificador único
        "filename": filename,
        "protocol": protocol.upper(),                         # normalización a mayúsculas
        "username": username or "No especificado",            # valor por defecto si vacío
        "size_kb": round(size_kb, 2),                        # dos decimales de precisión
        "status": status,
        "saved_path": saved_path,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
