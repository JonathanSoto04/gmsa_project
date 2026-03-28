"""Configuracion central de la aplicacion."""

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")


class Settings:
    """Contenedor de la configuracion global."""

    PROJECT_NAME: str = "Gestor Multiservicio de Almacenamiento"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "API local para gestionar la carga y administracion de archivos "
        "por multiples protocolos de almacenamiento."
    )

    CORS_ORIGINS: list[str] = ["*"]

    MAX_FILE_SIZE_MB: int = 10
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".csv",
            ".xlsx",
            ".zip",
        }
    )

    SUPPORTED_PROTOCOLS: frozenset[str] = frozenset({"nfs", "ftp", "s3", "smb"})

    TEMP_DIR: Path = _BACKEND_DIR / "temp"
    DATA_DIR: Path = _BACKEND_DIR / "data"
    HISTORY_FILE: Path = DATA_DIR / "history.json"
    UPLOAD_DIR: Path = _BACKEND_DIR / "uploads"

    S3_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "192.168.56.102:9000")
    S3_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
    S3_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "secret123")
    S3_BUCKET: str = os.getenv("MINIO_BUCKET_NAME", "storage-s3")
    S3_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

    FTP_HOST: str = os.getenv("FTP_HOST", "192.168.56.102")
    FTP_PORT: int = int(os.getenv("FTP_PORT", "21"))
    FTP_USER: str = os.getenv("FTP_USER", "ftpuser")
    FTP_PASS: str = os.getenv("FTP_PASS", "secret")
    FTP_DIR: str = os.getenv("FTP_DIR", "/")

    SMB_HOST: str = os.getenv("SMB_HOST", "192.168.56.102")
    SMB_USER: str = os.getenv("SMB_USER", "ftp_user")
    SMB_PASS: str = os.getenv("SMB_PASS", "secret")
    SMB_SHARE: str = os.getenv("SMB_SHARE", "smb")
    SMB_DIR: str = os.getenv("SMB_DIR", "/")
    SMB_DOMAIN: str = os.getenv("SMB_DOMAIN", "")

    NFS_HOST: str = os.getenv("NFS_HOST", "192.168.56.102")
    NFS_SSH_PORT: int = int(os.getenv("NFS_SSH_PORT", "22"))
    NFS_USER: str = os.getenv("NFS_USER", "ftpuser")
    NFS_PASS: str = os.getenv("NFS_PASS", "secret")
    NFS_DIR: str = os.getenv("NFS_DIR", "/mnt/prueba/nfs")

    def ensure_runtime_directories(self) -> None:
        """Crea los directorios locales requeridos por la aplicacion."""
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        for protocol in self.SUPPORTED_PROTOCOLS:
            self.get_protocol_upload_dir(protocol)

    def get_protocol_upload_dir(self, protocol: str) -> Path:
        """Retorna la carpeta local asociada a un protocolo soportado."""
        normalized = protocol.lower().strip()
        if normalized not in self.SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Protocolo '{protocol}' no valido. "
                f"Opciones: {', '.join(sorted(self.SUPPORTED_PROTOCOLS))}."
            )

        directory = self.UPLOAD_DIR / normalized
        directory.mkdir(parents=True, exist_ok=True)
        return directory


settings = Settings()
