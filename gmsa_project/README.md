# Gestor Multiservicio de Almacenamiento

Proyecto académico local con frontend en **Svelte 5 + Bootstrap 5** y backend en **Python + FastAPI**.
Arquitectura limpia por capas, preparada para integrar protocolos de almacenamiento reales.

## Objetivo

Construir una interfaz web local capaz de gestionar la carga de archivos mediante diferentes protocolos de almacenamiento:

| Protocolo | Descripción |
|-----------|-------------|
| NFS       | Almacenamiento compartido en red (Linux / rutas montadas) |
| FTP       | Transferencia tradicional con credenciales |
| SFTP      | Transferencia segura sobre SSH |
| S3 / MinIO | Almacenamiento tipo objeto compatible con Amazon S3 |
| SMB       | Recursos compartidos en entornos Windows |

## Flujo de la aplicación

```
Usuario → Frontend (Svelte 5) → Backend (FastAPI) → StorageHandler → Destino
```

## Características

- Dashboard tipo admin con indicador de estado de la API
- Selector de protocolo con tarjetas visuales por color
- Validación de extensión de archivo (12 tipos permitidos)
- Validación de tamaño máximo (10 MB), procesada en bloques de 1 MB
- Historial persistente en JSON con columnas: archivo, protocolo, tamaño, usuario, estado
- Botón para limpiar historial desde la interfaz
- Barra de progreso visual durante la carga
- Mensajes de éxito y error contextuales
- Arquitectura modular: agregar un protocolo real requiere un solo archivo nuevo

## Estructura del proyecto

```text
gmsa_project/
├── backend/
│   ├── app/
│   │   ├── main.py              # App factory: middleware y routers
│   │   ├── config.py            # Clase Settings con todas las constantes
│   │   ├── schemas.py           # Modelos Pydantic (request / response)
│   │   ├── routers/
│   │   │   ├── info.py          # GET /  y  GET /config
│   │   │   ├── upload.py        # POST /upload
│   │   │   └── history.py       # GET /history  y  DELETE /history
│   │   ├── services/
│   │   │   ├── upload_service.py   # Orquestación del flujo de carga
│   │   │   └── history_service.py  # Lectura / escritura del historial
│   │   └── storage/
│   │       ├── base.py          # Clase abstracta StorageHandler
│   │       ├── local.py         # Implementación local (simulación)
│   │       └── registry.py      # Mapa protocolo → handler (punto de extensión)
│   ├── data/
│   │   └── history.json         # Historial persistente
│   ├── uploads/                 # Carpetas creadas automáticamente al iniciar
│   │   ├── nfs/
│   │   ├── ftp/
│   │   ├── s3/
│   │   └── smb/
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── app.css
        ├── App.svelte            # Orquestador: estado compartido y layout
        ├── lib/
        │   ├── api.js            # Todas las llamadas fetch al backend
        │   └── config.js         # API_URL y constantes
        └── components/
            ├── Header.svelte
            ├── StatsBar.svelte
            ├── ProtocolSelector.svelte
            ├── UploadForm.svelte
            └── HistoryTable.svelte
```

## Requisitos previos (Windows)

- **Python 3.10 o superior** — [python.org/downloads](https://www.python.org/downloads/)
  Verificar: `python --version`
- **Node.js 18 o superior** — [nodejs.org](https://nodejs.org/)
  Verificar: `node --version` y `npm --version`

## Cómo ejecutar en Windows

Abrir **dos terminales separadas** (CMD, PowerShell o Windows Terminal).

### Terminal 1 — Backend

```cmd
cd ruta\al\proyecto\gmsa_project\backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API disponible en:
```
http://127.0.0.1:8000
```

Documentación interactiva (Swagger UI):
```
http://127.0.0.1:8000/docs
```

### Terminal 2 — Frontend

```cmd
cd ruta\al\proyecto\gmsa_project\frontend
npm install
npm run dev
```

Interfaz disponible en:
```
http://localhost:5173
```

> El backend debe estar corriendo antes de abrir el frontend.
> Si el indicador superior muestra "API desconectada", verificar que `uvicorn` esté activo.

## Punto de extensión para protocolos reales

Para integrar un protocolo real (ejemplo: FTP), solo se necesita:

1. Crear `backend/app/storage/ftp.py` con una clase que extienda `StorageHandler`.
2. Registrar esa clase en `backend/app/storage/registry.py`.

**Nada más cambia** — ni el frontend, ni los routers, ni los servicios.

```python
# storage/registry.py  (único archivo a modificar)
from app.storage.ftp import FTPStorageHandler

_REGISTRY = {
    "ftp":  FTPStorageHandler(host="...", user="...", password="..."),
    # resto sin cambios
}
```

## Tecnologías

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | Python + FastAPI | FastAPI 0.116 |
| Servidor ASGI | Uvicorn | 0.35 |
| Frontend | Svelte | 5.x |
| Bundler | Vite | 7.x |
| Estilos | Bootstrap + CSS custom | Bootstrap 5.3 |
| Iconos | Bootstrap Icons | 1.11 |
