"""
main.py
-------
Fábrica de la aplicación para la API del Gestor Multiservicio de Almacenamiento.

Responsabilidades de este archivo (y solo de este archivo):
  - Configurar el logging estructurado.
  - Instanciar la aplicación FastAPI.
  - Registrar el middleware de CORS.
  - Montar todos los routers.

La lógica de negocio se encuentra en services/.
La lógica de almacenamiento se encuentra en storage/.
Las definiciones de rutas se encuentran en routers/.

Ejecutar desde el directorio backend/ con:
    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import history, info, upload

# ---------------------------------------------------------------------------
# Configuración del logging
# Aquí se define el formato con el que se mostrarán los mensajes
# en consola, incluyendo fecha, nivel del log, nombre del módulo
# y mensaje correspondiente.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------------------------------------------------------------------------
# Creación de la instancia principal de FastAPI
# Se configura el nombre del proyecto, descripción, versión
# y las rutas de documentación automática.
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Configuración del middleware CORS
# Permite controlar qué orígenes pueden acceder al backend
# desde el frontend u otras aplicaciones.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Registro de routers
# Aquí se integran los módulos de rutas de la aplicación:
# - info: información general de la API
# - upload: carga de archivos
# - history: historial de cargas realizadas
# ---------------------------------------------------------------------------
app.include_router(info.router)
app.include_router(upload.router)
app.include_router(history.router)