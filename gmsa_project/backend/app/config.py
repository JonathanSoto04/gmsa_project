"""
config.py
---------
Central configuration for the application.

All tuneable constants live here as class attributes of `Settings`.
Import the singleton `settings` object anywhere in the app — never
import individual constants directly from this module.
"""

from pathlib import Path

# Absolute path to the backend/ directory (parent of app/).
_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # -------------------------------------------------------------------------
    # Application metadata
    # -------------------------------------------------------------------------
    PROJECT_NAME: str = "Gestor Multiservicio de Almacenamiento"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "API local para gestionar la carga de archivos "
        "por múltiples protocolos de almacenamiento."
    )

    # -------------------------------------------------------------------------
    # CORS
    # Restrict to specific origins in a production deployment.
    # -------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["*"]

    # -------------------------------------------------------------------------
    # File validation
    # -------------------------------------------------------------------------
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".pdf",
            ".doc", ".docx",
            ".txt", ".csv", ".xlsx", ".zip",
        }
    )

    SUPPORTED_PROTOCOLS: frozenset[str] = frozenset(
        {"nfs", "ftp", "sftp", "s3", "smb"}
    )

    # -------------------------------------------------------------------------
    # Filesystem paths
    # -------------------------------------------------------------------------
    TEMP_DIR: Path = _BACKEND_DIR / "temp"
    DATA_DIR: Path = _BACKEND_DIR / "data"
    HISTORY_FILE: Path = DATA_DIR / "history.json"
    UPLOAD_DIR: Path = _BACKEND_DIR / "uploads"


# Module-level singleton — import this everywhere.
settings = Settings()
