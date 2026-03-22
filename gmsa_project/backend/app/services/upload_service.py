"""
Archivo : services/upload_service.py
Descripción:
    Servicio que orquesta el flujo completo de carga de archivos.

    Contiene toda la lógica de negocio asociada a la subida de un archivo:
    validación de extensión, escritura temporal con control de tamaño,
    delegación al manejador de almacenamiento del protocolo elegido,
    registro del resultado en el historial y limpieza de archivos temporales.

Responsabilidades:
    - Validar la extensión del archivo contra la lista de tipos permitidos.
    - Recibir el flujo de bytes y escribirlo en un archivo temporal por fragmentos,
      controlando que no exceda el límite de tamaño configurado.
    - Invocar al manejador de almacenamiento correspondiente al protocolo.
    - Persistir el resultado (éxito o error) en el historial JSON.
    - Garantizar la eliminación del archivo temporal en cualquier escenario.

Arquitectura:
    Forma parte de la capa de servicios. Depende de:
        · app.config.settings              — para límites y extensiones válidas.
        · app.services.history_service     — para construir y persistir registros.
        · app.storage.registry.get_handler — para obtener el manejador del protocolo.

    Los errores de validación se elevan como HTTPException inmediatamente y
    NO se registran en el historial. Solo los fallos de almacenamiento reales
    generan un registro con estado "Error".
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.history_service import append_record, build_record
from app.storage.registry import get_handler

# Logger con el nombre del módulo para facilitar el filtrado en los logs.
logger = logging.getLogger(__name__)


async def process_upload(
    *,
    file: UploadFile,
    protocol: str,
    username: str,
) -> dict:
    """
    Ejecuta el pipeline completo de carga de un archivo.

    Flujo de ejecución:
        1. Validar la extensión del archivo.
        2. Escribir el contenido en un archivo temporal (1 MB por fragmento),
           abortando si se supera el límite de tamaño.
        3. Invocar al manejador de almacenamiento del protocolo seleccionado.
        4. Construir y persistir el registro de éxito en el historial.
        5. Eliminar el archivo temporal (en el bloque ``finally``).

    Parámetros (solo por nombre):
        file     : Objeto ``UploadFile`` proporcionado por FastAPI con el stream del archivo.
        protocol : Identificador del protocolo de almacenamiento (p. ej., ``"s3"``).
        username : Nombre del usuario que realiza la operación.

    Retorna:
        Diccionario con el registro de historial creado en caso de éxito.

    Lanza:
        HTTPException 422 — si la extensión no está permitida o se supera el tamaño máximo.
        HTTPException 500 — si ocurre un error inesperado en la capa de almacenamiento.
    """
    # Paso 1: verificar que la extensión del archivo sea válida.
    _validate_extension(file.filename)

    # Paso 2: escribir el stream en un archivo temporal con control de tamaño.
    temp_path, size_bytes = await _stream_to_temp(file)

    try:
        # Paso 3: obtener el manejador del protocolo y persistir el archivo.
        handler = get_handler(protocol)
        saved_path = handler.save(temp_path, file.filename)

        # Paso 4: construir el registro de éxito y guardarlo en el historial.
        record = build_record(
            filename=file.filename,
            protocol=protocol,
            username=username,
            size_kb=size_bytes / 1024,
            status="Éxito",
            saved_path=saved_path,
        )
        append_record(record)

        logger.info(
            "Upload OK — '%s' via %s (%.1f KB) by '%s'",
            file.filename,
            protocol.upper(),
            size_bytes / 1024,
            username or "anon",
        )
        return record

    except HTTPException:
        # Las HTTPException ya tienen el formato correcto; se propagan sin modificación.
        raise

    except Exception as exc:
        # Fallo inesperado en el almacenamiento: se registra el error en el historial
        # y se eleva una HTTPException 500 con el detalle del fallo.
        logger.error("Storage failure for '%s': %s", file.filename, exc)
        _record_error(file.filename, protocol, username, size_bytes)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el archivo via {protocol.upper()}: {exc}",
        )

    finally:
        # Paso 5: eliminar el archivo temporal independientemente del resultado.
        # ``missing_ok=True`` evita un error secundario si el archivo ya fue eliminado.
        temp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------

def _validate_extension(filename: str) -> None:
    """
    Verifica que la extensión del archivo esté en la lista de tipos permitidos.

    Parámetros:
        filename : Nombre original del archivo enviado por el cliente.

    Lanza:
        HTTPException 422 — si la extensión no está permitida o el archivo no
                            tiene extensión reconocible.
    """
    ext = Path(filename).suffix.lower()
    if not ext or ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Extensión '{ext or 'ninguna'}' no permitida. "
                f"Tipos aceptados: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
            ),
        )


async def _stream_to_temp(file: UploadFile) -> tuple[Path, int]:
    """
    Lee el stream del archivo cargado y lo escribe en un archivo temporal único.

    La lectura se realiza por fragmentos de 1 MB para mantener un consumo
    de memoria acotado independientemente del tamaño del archivo. Si el
    acumulado supera el límite configurado, el proceso se interrumpe
    inmediatamente y el archivo temporal se elimina.

    Parámetros:
        file : Objeto ``UploadFile`` con el stream de bytes del archivo.

    Retorna:
        Tupla ``(temp_path, size_bytes)`` donde ``temp_path`` es la ruta al
        archivo temporal creado y ``size_bytes`` es el tamaño total en bytes.

    Lanza:
        HTTPException 422 — si el archivo supera el límite de tamaño.
        HTTPException 500 — si ocurre un error de escritura en disco.
    """
    # Crear el directorio temporal si no existe.
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Generar un nombre único para evitar colisiones entre cargas concurrentes.
    temp_path = settings.TEMP_DIR / f"{uuid.uuid4()}_{file.filename}"
    size_bytes = 0

    try:
        with open(temp_path, "wb") as buf:
            # Lectura en fragmentos de 1 MB para controlar el uso de memoria.
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                # Control del límite de tamaño en tiempo de escritura.
                if size_bytes > settings.MAX_FILE_SIZE_BYTES:
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=422,
                        detail=f"El archivo supera el límite de {settings.MAX_FILE_SIZE_MB} MB.",
                    )
                buf.write(chunk)
    except HTTPException:
        raise
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error de escritura temporal: {exc}")

    return temp_path, size_bytes


def _record_error(
    filename: str, protocol: str, username: str, size_bytes: int
) -> None:
    """
    Persiste un registro de fallo en el historial de cargas.

    Se invoca únicamente cuando el error ocurre en la capa de almacenamiento,
    después de que la validación previa fue superada exitosamente.

    Parámetros:
        filename   : Nombre del archivo que falló al guardarse.
        protocol   : Protocolo que se intentó utilizar.
        username   : Nombre del usuario que inició la carga.
        size_bytes : Tamaño del archivo en bytes (0 si no se pudo determinar).
    """
    record = build_record(
        filename=filename,
        protocol=protocol,
        username=username,
        size_kb=size_bytes / 1024 if size_bytes else 0,
        status="Error",
        saved_path="-",
    )
    append_record(record)
