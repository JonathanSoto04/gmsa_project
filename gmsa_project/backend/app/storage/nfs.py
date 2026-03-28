"""StorageHandler para NFS accesible via SSH/SFTP."""

from __future__ import annotations

import logging
from pathlib import Path

import paramiko

from app.config import settings
from app.storage.base import (
    StorageAuthenticationError,
    StorageConfigurationError,
    StorageCredentials,
    StorageHandler,
    StoragePathError,
    StoragePermissionError,
)

logger = logging.getLogger(__name__)


class NFSStorageHandler(StorageHandler):
    """Sube y elimina archivos en el directorio NFS remoto."""

    def _get_ssh_client(self) -> paramiko.SSHClient:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            settings.NFS_HOST,
            port=settings.NFS_SSH_PORT,
            username=settings.NFS_USER,
            password=settings.NFS_PASS,
            timeout=10,
        )
        return ssh

    def save(
        self,
        temp_path: Path,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> str:
        safe_name = self._validate_filename(filename)
        ssh = None
        sftp = None

        try:
            ssh = self._get_ssh_client()
            sftp = ssh.open_sftp()

            remote_path = f"{settings.NFS_DIR.rstrip('/')}/{safe_name}"
            sftp.put(str(temp_path), remote_path)

            saved_path = f"nfs://{settings.NFS_HOST}{remote_path}"
            logger.info("NFSStorage save OK '%s' -> %s", safe_name, saved_path)
            return saved_path
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()

    def delete(
        self,
        filename: str,
        credentials: StorageCredentials | None = None,
    ) -> None:
        safe_name = self._validate_filename(filename)
        ssh = None
        sftp = None
        remote_path = f"{settings.NFS_DIR.rstrip('/')}/{safe_name}"

        try:
            ssh = self._get_ssh_client()
            sftp = ssh.open_sftp()
            sftp.remove(remote_path)
            logger.info("NFSStorage delete OK '%s' -> %s", safe_name, remote_path)
        except FileNotFoundError:
            logger.info("NFSStorage delete skipped '%s' because remote file was absent", safe_name)
        except PermissionError as exc:
            raise StoragePermissionError(
                "NFS rechazo la eliminacion del archivo. Verifica permisos sobre el directorio remoto."
            ) from exc
        except paramiko.AuthenticationException as exc:
            raise StorageAuthenticationError(
                "Autenticacion NFS/SSH rechazada. Verifica las credenciales configuradas."
            ) from exc
        except OSError as exc:
            if getattr(exc, "errno", None) == 2:
                logger.info("NFSStorage delete skipped '%s' because remote file was absent", safe_name)
                return
            if getattr(exc, "errno", None) == 13:
                raise StoragePermissionError(
                    "NFS rechazo la eliminacion del archivo. Verifica permisos sobre el directorio remoto."
                ) from exc
            raise StorageConfigurationError(f"Error NFS al eliminar '{safe_name}': {exc}") from exc
        except paramiko.SSHException as exc:
            raise StorageConfigurationError(f"Error NFS al eliminar '{safe_name}': {exc}") from exc
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()

    def _validate_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename or safe_name in {".", ".."}:
            raise StoragePathError(
                "El nombre del archivo NFS es invalido. No se permiten rutas embebidas ni '..'."
            )
        return safe_name
