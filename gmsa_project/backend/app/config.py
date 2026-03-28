"""
Archivo : config.py
Descripción:
    Módulo de configuración central de la aplicación.

    Centraliza todas las constantes configurables en los atributos de la
    clase ``Settings``. El objeto singleton ``settings`` debe importarse
    en cualquier módulo que necesite acceder a estos valores; nunca se
    deben importar las constantes individuales directamente.

Arquitectura:
    Este módulo es la única fuente de verdad para parámetros como rutas
    del sistema de archivos, límites de validación, protocolos admitidos
    y metadatos del proyecto. Al centralizar la configuración aquí se
    simplifica el mantenimiento y se evita la dispersión de valores
    mágicos por el código.

    Las credenciales de los protocolos se leen desde variables de entorno
    definidas en ``.env``. No se deben hardcodear secretos aquí.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Ruta absoluta al directorio backend/ (directorio padre de app/).
# Se calcula de forma dinámica para que el proyecto sea portable
# independientemente del directorio de trabajo del proceso.
_BACKEND_DIR = Path(__file__).resolve().parent.parent

# Carga el archivo .env del directorio backend/ antes de leer variables.
load_dotenv(_BACKEND_DIR / ".env")


class Settings:
    """
    Contenedor de la configuración global de la aplicación.

    Todos los atributos son constantes de clase; no se instancian por
    separado. Para acceder a ellos desde cualquier módulo se debe usar
    el singleton ``settings`` definido al final de este archivo.
    """

    # -------------------------------------------------------------------------
    # Metadatos del proyecto
    # Estos valores se exponen en la documentación automática de FastAPI
    # (Swagger UI y ReDoc) y en el endpoint de health check.
    # -------------------------------------------------------------------------
    PROJECT_NAME: str = "Gestor Multiservicio de Almacenamiento"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "API local para gestionar la carga de archivos "
        "por múltiples protocolos de almacenamiento."
    )

    # -------------------------------------------------------------------------
    # Configuración de CORS (Cross-Origin Resource Sharing)
    # En entornos de producción se deben restringir los orígenes permitidos
    # a los dominios específicos del frontend para mejorar la seguridad.
    # El valor ['*'] es adecuado únicamente para desarrollo local.
    # -------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["*"]

    # -------------------------------------------------------------------------
    # Validación de archivos
    # Define los límites y tipos de archivo aceptados por el sistema.
    # Estos valores se utilizan tanto en el servicio de carga como en el
    # endpoint /config para informar al frontend qué puede enviar.
    # -------------------------------------------------------------------------

    # Tamaño máximo permitido expresado en megabytes y en bytes.
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Extensiones de archivo permitidas. Se usa frozenset para garantizar
    # inmutabilidad y consultas O(1).
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".pdf",
            ".doc", ".docx",
            ".txt", ".csv", ".xlsx", ".zip",
        }
    )

    # Protocolos de almacenamiento soportados por la aplicación.
    # SFTP queda excluido de esta integración.
    SUPPORTED_PROTOCOLS: frozenset[str] = frozenset(
        {"nfs", "ftp", "s3", "smb"}
    )

    # -------------------------------------------------------------------------
    # Rutas del sistema de archivos
    # Todas las rutas se construyen de forma relativa a _BACKEND_DIR para
    # garantizar portabilidad entre sistemas operativos y entornos.
    # -------------------------------------------------------------------------

    # Directorio temporal donde se almacenan los archivos durante la subida
    # antes de ser movidos al destino definitivo.
    TEMP_DIR: Path = _BACKEND_DIR / "temp"

    # Directorio donde se almacena el archivo de historial JSON.
    DATA_DIR: Path = _BACKEND_DIR / "data"

    # Ruta completa al archivo de historial de cargas.
    HISTORY_FILE: Path = DATA_DIR / "history.json"

    # Directorio raíz donde cada protocolo tiene su subcarpeta de destino.
    UPLOAD_DIR: Path = _BACKEND_DIR / "uploads"

    # -------------------------------------------------------------------------
    # S3 / MinIO
    # -------------------------------------------------------------------------
    S3_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "192.168.56.102:9000")
    S3_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
    S3_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "secret123")
    S3_BUCKET: str = os.getenv("MINIO_BUCKET_NAME", "storage-s3")
    S3_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

    # -------------------------------------------------------------------------
    # FTP
    # -------------------------------------------------------------------------
    FTP_HOST: str = os.getenv("FTP_HOST", "192.168.56.102")
    FTP_PORT: int = int(os.getenv("FTP_PORT", "21"))
    FTP_USER: str = os.getenv("FTP_USER", "ftpuser")
    FTP_PASS: str = os.getenv("FTP_PASS", "secret")
    FTP_DIR: str = os.getenv("FTP_DIR", "/")

    # -------------------------------------------------------------------------
    # SMB
    # -------------------------------------------------------------------------
    SMB_HOST: str = os.getenv("SMB_HOST", "192.168.56.102")
    SMB_USER: str = os.getenv("SMB_USER", "ftp_user")
    SMB_PASS: str = os.getenv("SMB_PASS", "secret")
    SMB_SHARE: str = os.getenv("SMB_SHARE", "smb")
    SMB_DIR: str = os.getenv("SMB_DIR", "/")
    SMB_DOMAIN: str = os.getenv("SMB_DOMAIN", "")

    # -------------------------------------------------------------------------
    # NFS (accedido vía SSH; no requiere montaje local)
    # -------------------------------------------------------------------------
    NFS_HOST: str = os.getenv("NFS_HOST", "192.168.56.102")
    NFS_SSH_PORT: int = int(os.getenv("NFS_SSH_PORT", "22"))
    NFS_USER: str = os.getenv("NFS_USER", "ftpuser")
    NFS_PASS: str = os.getenv("NFS_PASS", "secret")
    NFS_DIR: str = os.getenv("NFS_DIR", "/mnt/prueba/nfs")


# Singleton del módulo — debe importarse en lugar de la clase directamente.
# Uso correcto:   from app.config import settings
# Uso incorrecto: from app.config import Settings
settings = Settings()
