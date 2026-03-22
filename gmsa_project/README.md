# Gestor Multiservicio de Almacenamiento

Proyecto académico local con frontend en **Svelte + Bootstrap + CSS** y backend en **Python + FastAPI**.

## Objetivo
Construir una interfaz web local capaz de gestionar la carga de archivos según diferentes servicios de almacenamiento:
- NFS
- FTP
- SFTP
- S3 / MinIO
- SMB

## Arquitectura
Usuario -> Página web -> Backend FastAPI -> Protocolo correspondiente

## Características implementadas
- Dashboard moderno tipo admin
- Selección de protocolo mediante tarjetas
- Validación por extensión
- Validación por tamaño máximo (10 MB)
- Carga de archivos al backend
- Historial persistente en `history.json`
- Barra de progreso visual
- Mensajes de éxito y error
- Código documentado para exposición y mantenimiento

## Estructura
```text
backend/
  main.py
  storage_handlers.py
  history.json
  requirements.txt
  uploads/
    nfs/
    ftp/
    s3/
    smb/
frontend/
  package.json
  vite.config.js
  index.html
  src/
    main.js
    App.svelte
    app.css
```

## Cómo ejecutar

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API disponible en:
```text
http://127.0.0.1:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend disponible normalmente en:
```text
http://localhost:5173
```

## Nota técnica importante
Actualmente el sistema guarda los archivos en carpetas locales separadas por protocolo.
Esto se hizo para dejar lista tu parte del proyecto web.

Luego, tu compañero puede reemplazar la función `save_file_by_protocol()` en `storage_handlers.py`
para conectar:
- NFS real
- FTP / SFTP real
- S3 / MinIO real
- SMB real

Sin cambiar la interfaz ni el flujo general.
