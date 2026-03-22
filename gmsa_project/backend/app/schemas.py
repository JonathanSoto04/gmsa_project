"""
Archivo : schemas.py
Descripción:
    Modelos Pydantic utilizados para la validación de solicitudes entrantes
    y la serialización de respuestas salientes de la API.

    Concentrar todas las estructuras de datos en este módulo facilita su
    localización, actualización y reutilización entre distintos routers sin
    necesidad de importar desde módulos no relacionados.

Arquitectura:
    Cada clase hereda de ``pydantic.BaseModel``, lo que garantiza validación
    automática de tipos, serialización a JSON y generación de esquemas
    OpenAPI para la documentación interactiva de FastAPI.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UploadRecord(BaseModel):
    """
    Representa un único registro del historial de cargas.

    Atributos:
        id          : Identificador único UUID generado en el momento de la carga.
        filename    : Nombre original del archivo enviado por el cliente.
        protocol    : Protocolo de almacenamiento utilizado (en mayúsculas).
        username    : Nombre del usuario que realizó la operación.
        size_kb     : Tamaño del archivo en kilobytes, redondeado a dos decimales.
        status      : Resultado de la operación; puede ser ``"Éxito"`` o ``"Error"``.
        saved_path  : Ruta o identificador donde quedó almacenado el archivo.
        uploaded_at : Marca de tiempo de la operación en formato ``YYYY-MM-DD HH:MM:SS``.
    """

    id: str
    filename: str
    protocol: str
    username: str
    size_kb: float
    status: Literal["Éxito", "Error"]
    saved_path: str
    uploaded_at: str


class UploadResponse(BaseModel):
    """
    Respuesta devuelta por el endpoint ``POST /upload`` tras procesar un archivo.

    Atributos:
        success : Indicador booleano del resultado de la operación.
        message : Mensaje descriptivo para mostrar al usuario final.
        record  : Registro completo de la carga persistido en el historial.
    """

    success: bool
    message: str
    record: UploadRecord


class HistoryResponse(BaseModel):
    """
    Respuesta devuelta por el endpoint ``GET /history``.

    Atributos:
        total : Número total de registros devueltos.
        items : Lista de registros de carga ordenados del más reciente al más antiguo.
    """

    total: int
    items: list[UploadRecord]


class ConfigResponse(BaseModel):
    """
    Respuesta devuelta por el endpoint ``GET /config``.

    Expone al frontend los parámetros de configuración necesarios para
    conducir el comportamiento de la interfaz de usuario: tamaño máximo,
    extensiones permitidas y protocolos disponibles.

    Atributos:
        project_name         : Nombre oficial del proyecto.
        max_file_size_mb     : Límite de tamaño de archivo en megabytes.
        allowed_extensions   : Lista ordenada de extensiones de archivo aceptadas.
        supported_protocols  : Lista ordenada de protocolos de almacenamiento disponibles.
    """

    project_name: str
    max_file_size_mb: int
    allowed_extensions: list[str]
    supported_protocols: list[str]
