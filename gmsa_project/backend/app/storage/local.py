"""
Archivo : storage/local.py
Descripción:
    Manejador de almacenamiento local que simula el comportamiento de un
    protocolo remoto copiando los archivos a un subdirectorio local.

    En lugar de realizar una transferencia real de red (FTP, SFTP, S3, etc.),
    este manejador copia el archivo temporal al directorio de destino
    correspondiente al protocolo simulado. Esto permite desarrollar y
    demostrar la funcionalidad completa del sistema sin depender de
    servicios externos.

Responsabilidades:
    - Crear el directorio de destino del protocolo si no existe.
    - Copiar el archivo temporal al directorio de destino.
    - Retornar la ruta absoluta final del archivo almacenado.

Arquitectura:
    Implementa la interfaz ``StorageHandler`` de ``storage/base.py``.
    Es la única implementación concreta actual; está registrada para todos
    los protocolos en ``storage/registry.py``.

    Cuando se integre un protocolo real, se debe:
        1. Crear una subclase de ``StorageHandler`` específica para ese protocolo.
        2. Reemplazar o complementar el registro en ``storage/registry.py``.
        3. Este manejador local puede mantenerse para los protocolos que aún
           no tengan implementación real.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.config import settings
from app.storage.base import StorageCredentials, StorageHandler

# Logger con el nombre del módulo para facilitar la trazabilidad.
logger = logging.getLogger(__name__)


class LocalStorageHandler(StorageHandler):
    """
    Manejador de almacenamiento que persiste archivos en el sistema de archivos local,
    simulando el comportamiento de un destino de almacenamiento remoto.

    Cada instancia está asociada a un subdirectorio específico dentro de
    ``settings.UPLOAD_DIR``, de modo que cada protocolo simulado mantiene
    sus archivos organizados de forma independiente.

    Parámetros de inicialización:
        subfolder : Nombre del subdirectorio dentro de ``settings.UPLOAD_DIR``
                    al que este manejador escribirá los archivos.
                    Ejemplos: ``"nfs"``, ``"s3"``, ``"smb"``.
    """

    def __init__(self, subfolder: str) -> None:
        # Construir la ruta de destino y crearla si no existe.
        self._dest: Path = settings.UPLOAD_DIR / subfolder
        self._dest.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        """
        Copia el archivo temporal al directorio de destino del protocolo simulado.

        Parámetros:
            temp_path : Ruta al archivo temporal generado durante la carga.
            filename  : Nombre original del archivo; se usa como nombre de destino.

        Retorna:
            Cadena con la ruta absoluta resuelta donde quedó almacenado el archivo.

        Lanza:
            OSError — si ocurre un fallo al copiar el archivo en disco.
        """
        destination = self._dest / filename
        shutil.copy(temp_path, destination)
        logger.info("LocalStorage: '%s' → %s", filename, destination)
        return str(destination.resolve())
