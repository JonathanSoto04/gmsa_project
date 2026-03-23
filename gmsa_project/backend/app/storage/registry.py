"""
Archivo : storage/registry.py
Descripción:
    Registro centralizado que mapea identificadores de protocolo con sus
    respectivas instancias de manejadores de almacenamiento.

    Este módulo es el único punto del sistema donde se debe realizar el
    cambio al integrar un protocolo de almacenamiento real. El resto de
    la aplicación obtiene el manejador a través de ``get_handler()`` sin
    conocer ni depender de la implementación concreta.

Responsabilidades:
    - Mantener el mapeo ``protocolo → instancia de StorageHandler``.
    - Proporcionar la función ``get_handler()`` para obtener el manejador
      correspondiente a un protocolo dado.

Arquitectura:
    Forma parte de la capa de almacenamiento. Implementa el patrón
    Registry combinado con Strategy: las implementaciones son
    intercambiables y el sistema de selección está centralizado aquí.

    Para añadir o reemplazar un manejador:
        1. Crear la subclase en ``storage/<protocolo>.py``.
        2. Instanciarla en el diccionario ``_REGISTRY`` a continuación.
        3. No es necesario modificar ningún otro módulo.

    SFTP queda excluido intencionalmente de este registro.
"""

from __future__ import annotations

from app.storage.base import StorageHandler
from app.storage.ftp import FTPStorageHandler
from app.storage.nfs import NFSStorageHandler
from app.storage.s3 import S3StorageHandler
from app.storage.smb import SMBStorageHandler

# ---------------------------------------------------------------------------
# Registro de protocolos → manejadores reales
# ---------------------------------------------------------------------------
_REGISTRY: dict[str, StorageHandler] = {
    "s3": S3StorageHandler(),
    "ftp": FTPStorageHandler(),
    "smb": SMBStorageHandler(),
    "nfs": NFSStorageHandler(),
}


def get_handler(protocol: str) -> StorageHandler:
    """
    Retorna el manejador de almacenamiento registrado para el protocolo dado.

    Parámetros:
        protocol : Identificador del protocolo en minúsculas (p. ej., ``"s3"``).

    Retorna:
        Instancia de ``StorageHandler`` asociada al protocolo.

    Lanza:
        ValueError — si el protocolo no tiene un manejador registrado.
                     En producción esta excepción no debería alcanzarse porque
                     el router valida el protocolo antes de llamar a este módulo.
    """
    handler = _REGISTRY.get(protocol.lower())
    if handler is None:
        raise ValueError(
            f"No hay manejador de almacenamiento registrado para el protocolo: '{protocol}'"
        )
    return handler