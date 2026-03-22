"""
Archivo : storage/base.py
Descripción:
    Define la clase base abstracta que establece el contrato que todo
    manejador de almacenamiento debe implementar.

    Cualquier protocolo de almacenamiento real (FTP, SFTP, S3, NFS, SMB)
    debe existir como una subclase de ``StorageHandler`` que implemente
    el método ``save()``. Una vez creada la subclase, se registra en
    ``storage/registry.py`` sin necesidad de modificar ningún otro módulo.

Arquitectura:
    Forma parte de la capa de almacenamiento. Es la base del patrón
    Strategy utilizado para intercambiar implementaciones de protocolos
    de forma transparente para el resto de la aplicación.

    Para integrar un protocolo real, seguir los siguientes pasos:

        1. Crear el archivo ``storage/<protocolo>.py``.
        2. Definir una clase que herede de ``StorageHandler``.
        3. Implementar el método ``save()`` con la lógica del protocolo.
        4. Registrar la instancia en ``storage/registry.py``.

    Ejemplo — integración de un servidor FTP real:

        # storage/ftp.py
        from ftplib import FTP
        from app.storage.base import StorageHandler

        class FTPStorageHandler(StorageHandler):
            def __init__(self, host: str, user: str, password: str) -> None:
                self._host = host
                self._user = user
                self._password = password

            def save(self, temp_path: Path, filename: str) -> str:
                with FTP(self._host) as ftp:
                    ftp.login(self._user, self._password)
                    with open(temp_path, "rb") as f:
                        ftp.storbinary(f"STOR {filename}", f)
                return f"ftp://{self._host}/{filename}"

        # En storage/registry.py, reemplazar la línea correspondiente:
        "ftp": FTPStorageHandler(host="...", user="...", password="..."),
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageHandler(ABC):
    """
    Clase base abstracta para todos los manejadores de almacenamiento.

    Define el contrato mínimo que debe satisfacer cualquier implementación
    de protocolo de almacenamiento dentro de la aplicación. Al utilizar
    una interfaz común, el servicio de carga puede invocar ``save()`` sin
    conocer los detalles del protocolo subyacente.
    """

    @abstractmethod
    def save(self, temp_path: Path, filename: str) -> str:
        """
        Persiste el archivo ubicado en ``temp_path`` en el destino del protocolo.

        Las subclases concretas son responsables de implementar la lógica
        de transferencia específica de cada protocolo (FTP, SFTP, S3, etc.).

        Parámetros:
            temp_path : Ruta al archivo temporal creado por el servicio de carga.
                        El archivo existe en disco en el momento de llamar a este método.
            filename  : Nombre original del archivo proporcionado por el cliente.
                        Se utiliza como nombre de destino en el almacenamiento.

        Retorna:
            Cadena de texto que identifica la ubicación final del archivo:
            puede ser una ruta absoluta, una URL, una clave de bucket S3, etc.

        Lanza:
            Cualquier excepción de I/O o comunicación propia del protocolo.
            El servicio de carga captura estas excepciones y las convierte
            en HTTPException 500.
        """
        ...
