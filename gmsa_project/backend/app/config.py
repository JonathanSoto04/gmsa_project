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
"""

from pathlib import Path

# Ruta absoluta al directorio backend/ (directorio padre de app/).
# Se calcula de forma dinámica para que el proyecto sea portable
# independientemente del directorio de trabajo del proceso.
_BACKEND_DIR = Path(__file__).resolve().parent.parent


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
    # El valor ["*"] es adecuado únicamente para desarrollo local.
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
            ".jpg", ".jpeg", ".png", ".gif", ".webp",   # imágenes
            ".pdf",                                      # documentos PDF
            ".doc", ".docx",                             # documentos Word
            ".txt", ".csv", ".xlsx", ".zip",             # datos y comprimidos
        }
    )

    # Protocolos de almacenamiento soportados por la aplicación.
    # Cualquier protocolo que no figure aquí será rechazado en la validación
    # del endpoint de carga antes de llegar a la capa de almacenamiento.
    SUPPORTED_PROTOCOLS: frozenset[str] = frozenset(
        {"nfs", "ftp", "sftp", "s3", "smb"}
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


# Singleton del módulo — debe importarse en lugar de la clase directamente.
# Uso correcto:   from app.config import settings
# Uso incorrecto: from app.config import Settings
settings = Settings()
