"""
main.py
-------
API principal del proyecto:
    Gestor Multiservicio de Almacenamiento

Tecnologías:
- FastAPI para exponer endpoints REST.
- CORS para permitir consumo desde el frontend Svelte en localhost.
- Manejo de archivos y validaciones por tamaño/extensión.
- Registro persistente de historial en un archivo JSON local.

Arquitectura del flujo:
    Usuario -> Página web -> Backend FastAPI -> Capa de protocolo -> Destino

Objetivo académico:
- Simular y organizar la carga de archivos por protocolo.
- Permitir que la capa de conexión real sea integrada por otra persona del equipo
  sin modificar la interfaz ni el flujo principal.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from storage_handlers import save_file_by_protocol

# -----------------------------------------------------------------------------
# Configuración general de la aplicación
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Gestor Multiservicio de Almacenamiento API",
    description="API local para gestionar carga de archivos por múltiples protocolos.",
    version="1.0.0",
)

# Permite que el frontend local (por ejemplo Vite en localhost:5173) pueda
# consumir la API sin bloqueo por CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Rutas del proyecto
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

HISTORY_FILE = BASE_DIR / "history.json"
if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]", encoding="utf-8")

# Extensiones permitidas.
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf",
    ".doc", ".docx",
    ".txt", ".csv", ".xlsx", ".zip"
}

# Tamaño máximo: 10 MB
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_PROTOCOLS = {"nfs", "ftp", "sftp", "s3", "smb"}


# -----------------------------------------------------------------------------
# Utilidades internas
# -----------------------------------------------------------------------------
def load_history() -> list[dict]:
    """Carga el historial desde el archivo JSON local."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def save_history(history: list[dict]) -> None:
    """Guarda el historial completo en el archivo JSON local."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2, ensure_ascii=False)


def append_history(record: dict) -> None:
    """Agrega un registro nuevo al historial sin perder los anteriores."""
    history = load_history()
    history.append(record)
    save_history(history)


def build_record(
    *,
    filename: str,
    protocol: str,
    username: str,
    size_kb: float,
    status: str,
    saved_path: str,
) -> dict:
    """
    Construye un registro uniforme para el historial.
    Esto ayuda a mantener la misma estructura para éxitos y errores.
    """
    return {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "protocol": protocol.upper(),
        "username": username or "No especificado",
        "size_kb": round(size_kb, 2),
        "status": status,
        "saved_path": saved_path,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root() -> dict:
    """Endpoint de verificación rápida de la API."""
    return {
        "message": "Gestor Multiservicio de Almacenamiento API funcionando correctamente"
    }


@app.get("/config")
def get_config() -> dict:
    """
    Retorna la configuración útil para el frontend.
    Permite mostrar límites y tipos permitidos de forma dinámica.
    """
    return {
        "project_name": "Gestor Multiservicio de Almacenamiento",
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
        "supported_protocols": sorted(SUPPORTED_PROTOCOLS),
    }


@app.get("/history")
def get_history() -> dict:
    """Devuelve el historial en orden inverso para ver lo más reciente primero."""
    history = load_history()
    return {"items": history[::-1]}


@app.post("/upload")
async def upload_file(
    protocol: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
    file: UploadFile = File(...),
):
    """
    Endpoint principal de carga de archivos.

    Recibe:
    - protocol: protocolo seleccionado por el usuario.
    - username: usuario digitado en la interfaz.
    - password: contraseña digitada (recibida para simulación / futura integración).
    - file: archivo a cargar.

    Validaciones realizadas:
    - Protocolo permitido.
    - Extensión permitida.
    - Tamaño máximo.

    Después:
    - Guarda temporalmente el archivo.
    - Llama a la capa de almacenamiento.
    - Registra el resultado en historial.
    """
    protocol = protocol.lower().strip()

    if protocol not in SUPPORTED_PROTOCOLS:
        raise HTTPException(status_code=400, detail="Protocolo no válido.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Extensión detectada: {extension}",
        )

    temp_name = f"{uuid.uuid4()}_{file.filename}"
    temp_path = TEMP_DIR / temp_name
    size_bytes = 0

    try:
        # Guardado temporal por bloques para controlar tamaño y evitar usar mucha RAM.
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_FILE_SIZE_BYTES:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"El archivo supera el límite de {MAX_FILE_SIZE_MB} MB.",
                    )
                buffer.write(chunk)

        # Se unifica FTP y SFTP en la misma carpeta lógica de pruebas.
        internal_protocol = "ftp" if protocol in {"ftp", "sftp"} else protocol

        # Aquí ocurre la integración con la capa de almacenamiento.
        saved_path = save_file_by_protocol(
            protocol=internal_protocol,
            temp_file_path=temp_path,
            filename=file.filename,
        )

        success_record = build_record(
            filename=file.filename,
            protocol=protocol,
            username=username,
            size_kb=size_bytes / 1024,
            status="Éxito",
            saved_path=saved_path,
        )
        append_history(success_record)

        # Limpieza de archivo temporal.
        temp_path.unlink(missing_ok=True)

        return JSONResponse(
            {
                "success": True,
                "message": f"Archivo subido correctamente por {protocol.upper()}",
                "record": success_record,
            }
        )

    except HTTPException as exc:
        error_record = build_record(
            filename=file.filename,
            protocol=protocol,
            username=username,
            size_kb=size_bytes / 1024 if size_bytes else 0,
            status="Error",
            saved_path="-",
        )
        append_history(error_record)
        raise exc

    except Exception as exc:  # noqa: BLE001 - manejo controlado para demo académica
        temp_path.unlink(missing_ok=True)
        error_record = build_record(
            filename=file.filename,
            protocol=protocol,
            username=username,
            size_kb=size_bytes / 1024 if size_bytes else 0,
            status="Error",
            saved_path="-",
        )
        append_history(error_record)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(exc)}")
