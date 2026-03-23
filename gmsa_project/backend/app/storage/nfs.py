"""
storage/nfs.py
--------------
StorageHandler para NFS (acceso vía SSH/SFTP con paramiko).

No requiere un mount NFS local. Conecta por SSH al servidor TrueNAS,
abre un canal SFTP y deposita el archivo en el directorio NFS remoto.
Lee credenciales desde settings (que a su vez las carga del .env).

Nota: el protocolo de transporte es SSH/SFTP internamente, pero el
destino es el dataset NFS — el protocolo expuesto al usuario es "NFS".
SFTP como opción de usuario está excluido del sistema.
"""

from __future__ import annotations

import logging
from pathlib import Path

import paramiko

from app.config import settings
from app.storage.base import StorageHandler

logger = logging.getLogger(__name__)


class NFSStorageHandler(StorageHandler):
    """Sube archivos al directorio NFS remoto vía SSH/SFTP."""

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

    def save(self, temp_path: Path, filename: str) -> str:
        ssh = None
        try:
            ssh = self._get_ssh_client()
            sftp = ssh.open_sftp()

            remote_path = f"{settings.NFS_DIR}/{filename}"
            sftp.put(str(temp_path), remote_path)
            sftp.close()

            saved_path = f"nfs://{settings.NFS_HOST}{remote_path}"
            logger.info("NFSStorage: '%s' → %s", filename, saved_path)
            return saved_path
        finally:
            if ssh:
                ssh.close()
