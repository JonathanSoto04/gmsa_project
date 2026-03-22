"""
storage_handlers.py
-------------------
Capa de almacenamiento del proyecto.

Este archivo centraliza la lógica que decide dónde guardar un archivo según
el protocolo seleccionado desde la interfaz web.

IMPORTANTE:
- Actualmente esta versión guarda los archivos en carpetas locales separadas
  por protocolo, lo cual permite probar el flujo completo del sistema.
- Más adelante, esta misma capa puede ser reemplazada o extendida para usar
  conexiones reales con:
    * NFS montado en Windows
    * FTP / SFTP con credenciales reales
    * Bucket S3 / MinIO
    * SMB sobre recursos compartidos

De esta forma, el frontend y el backend principal NO necesitan reescribirse;
solo se adapta esta capa de integración.
"""

from pathlib import Path
import shutil

# Directorio base donde se almacenan las simulaciones de subida.
BASE_UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"

# Mapa de carpetas por protocolo.
PROTOCOL_DIRS = {
    "nfs": BASE_UPLOAD_DIR / "nfs",
    "ftp": BASE_UPLOAD_DIR / "ftp",
    "s3": BASE_UPLOAD_DIR / "s3",
    "smb": BASE_UPLOAD_DIR / "smb",
}

# Asegura que todas las carpetas existan antes de usarlas.
for folder in PROTOCOL_DIRS.values():
    folder.mkdir(parents=True, exist_ok=True)


def save_file_by_protocol(protocol: str, temp_file_path: Path, filename: str) -> str:
    """
    Guarda un archivo en la carpeta correspondiente según el protocolo.

    Parámetros:
        protocol (str): protocolo lógico seleccionado (nfs, ftp, s3, smb).
        temp_file_path (Path): ruta temporal donde FastAPI almacenó el archivo.
        filename (str): nombre original del archivo.

    Retorna:
        str: ruta absoluta donde finalmente quedó guardado.

    Flujo actual:
        1. Validar protocolo.
        2. Seleccionar carpeta destino.
        3. Copiar archivo temporal a la carpeta definitiva.
        4. Retornar ruta final.

    Punto de extensión real:
        - NFS: copiar al path montado en Windows.
        - FTP/SFTP: abrir conexión y hacer upload remoto.
        - S3/MinIO: usar SDK boto3/minio.
        - SMB: guardar en recurso compartido autenticado.
    """
    protocol = protocol.lower().strip()

    if protocol not in PROTOCOL_DIRS:
        raise ValueError(f"Protocolo no soportado: {protocol}")

    destination = PROTOCOL_DIRS[protocol] / filename
    shutil.copy(temp_file_path, destination)

    return str(destination.resolve())
