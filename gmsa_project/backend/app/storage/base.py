"""Contrato base y errores de la capa de almacenamiento."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorageCredentials:
    """Credenciales opcionales asociadas al request actual."""

    username: str = ""
    password: str = ""


class StorageError(Exception):
    """Excepcion base para errores controlados de almacenamiento."""


class StorageAuthenticationError(StorageError):
    """El servidor rechazo las credenciales o la autenticacion."""


class StoragePermissionError(StorageError):
    """La cuenta autenticada no tiene permisos sobre el destino."""


class StoragePathError(StorageError):
    """La ruta remota es invalida, no existe o no es accesible."""


class StorageConfigurationError(StorageError):
    """La configuracion local del protocolo es incompleta o invalida."""


class StorageHandler(ABC):
    """Contrato comun para cualquier backend de almacenamiento."""

    @abstractmethod
    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        """Persiste ``temp_path`` en el destino del protocolo y retorna la ruta final."""
        ...

    @abstractmethod
    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        """Elimina ``filename`` del destino del protocolo."""
        ...

    @abstractmethod
    def list_files(
        self,
        credentials: StorageCredentials | None = None,
    ) -> list[dict]:
        """Lista los archivos disponibles en el destino del protocolo."""
        ...
