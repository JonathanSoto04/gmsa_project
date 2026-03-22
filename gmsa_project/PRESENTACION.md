# Script de Presentación Técnica
## Gestor Multiservicio de Almacenamiento

---

### 1. Introducción (30 segundos)

> "El proyecto es una aplicación web local que permite cargar archivos a través de cinco protocolos de almacenamiento diferentes: NFS, FTP, SFTP, S3/MinIO y SMB.
> El objetivo principal no es solo que funcione, sino que esté construido con una arquitectura que permita integrar protocolos reales en el futuro sin tener que reescribir nada de lo existente."

---

### 2. Arquitectura general (45 segundos)

> "El flujo es simple: el usuario interactúa con el frontend hecho en Svelte 5, que se comunica con una API REST construida en FastAPI. Esa API delega el almacenamiento a una capa de handlers específicos por protocolo.
>
> La arquitectura está dividida en capas bien separadas:
> - **Routers** — definen los endpoints HTTP, nada más.
> - **Services** — contienen la lógica de negocio: orquestación de la carga, lectura y escritura del historial.
> - **Storage** — capa de almacenamiento con una clase abstracta que cada protocolo implementa de forma independiente."

---

### 3. Backend — Estructura y decisiones (60 segundos)

> "En el backend, el punto de entrada es `app/main.py`, que solo registra middleware y routers. Ninguna lógica de negocio vive ahí.
>
> Hay tres routers:
> - `/config` — devuelve configuración al frontend: extensiones permitidas y tamaño máximo.
> - `/upload` — recibe el archivo y lo pasa al servicio de carga.
> - `/history` — permite consultar y limpiar el historial.
>
> El servicio de carga, `upload_service.py`, maneja todo el flujo: valida la extensión, transmite el archivo en bloques de 1 MB para controlar memoria, llama al handler del protocolo correspondiente y registra el resultado.
>
> Una decisión importante: los errores de validación —extensión incorrecta, archivo muy grande— no se guardan en el historial. Solo se registran los intentos genuinos de almacenamiento. Esto mantiene el historial limpio y significativo.
>
> Todos los modelos de request y response están definidos con Pydantic, lo que genera documentación automática en `/docs` y valida los datos en ambas direcciones."

---

### 4. Capa de almacenamiento — Escalabilidad (45 segundos)

> "La parte más importante de la arquitectura es la capa de storage.
>
> Existe una clase abstracta `StorageHandler` con un único método: `save()`. Actualmente la implementación es `LocalStorageHandler`, que copia el archivo a una carpeta local simulando cada protocolo.
>
> El mapa que relaciona cada protocolo con su handler está en `registry.py`. Cuando mi compañero quiera integrar FTP real, solo necesita:
> 1. Crear una clase `FTPStorageHandler` que extienda la clase base.
> 2. Registrarla en el mapa con una sola línea.
>
> El frontend, los routers y los servicios no cambian absolutamente nada."

---

### 5. Frontend — Componentes y UX (45 segundos)

> "El frontend está hecho con Svelte 5, usando la API de runes que es la forma moderna de manejar reactividad en esta versión.
>
> La interfaz está descompuesta en cinco componentes:
> - **Header** — muestra el nombre del proyecto y un indicador de estado de la API en tiempo real.
> - **StatsBar** — cuatro tarjetas con métricas del historial: total, exitosas, errores y último protocolo usado.
> - **ProtocolSelector** — tarjetas de selección con colores diferenciados por protocolo.
> - **UploadForm** — maneja credenciales, archivo, barra de progreso y mensajes de respuesta.
> - **HistoryTable** — tabla con cinco columnas y un botón para limpiar el historial.
>
> Toda la comunicación con el backend está centralizada en `lib/api.js`. Ningún componente hace un `fetch` directamente."

---

### 6. Validaciones (30 segundos)

> "Las validaciones ocurren en dos niveles.
>
> En el **frontend**, antes de enviar: se verifica la extensión contra la lista que devuelve el backend, y el tamaño contra el límite configurado. Esto da feedback inmediato al usuario sin consumir red.
>
> En el **backend**, como segunda línea de defensa: se validan los mismos criterios. El archivo se lee en bloques de 1 MB, y si en algún momento supera el límite, se descarta el archivo temporal y se retorna un error 422.
>
> Esto garantiza que ni la red ni la memoria se saturen con archivos inválidos."

---

### 7. Cierre y escalabilidad (30 segundos)

> "En resumen, el sistema está diseñado para que la parte web —que es nuestra responsabilidad— esté completamente terminada y sea independiente de los protocolos de red.
>
> Cualquier miembro del equipo puede integrar NFS real, un bucket de MinIO, o un servidor SFTP sin tocar una sola línea del frontend ni de los servicios existentes.
>
> La arquitectura no es la más simple posible, pero es la mínima necesaria para que el sistema sea mantenible, extensible y fácil de explicar."

---

### Posibles preguntas y respuestas

**¿Por qué FastAPI y no Flask?**
> FastAPI incluye validación automática con Pydantic, documentación Swagger generada, soporte async nativo y tipado estático. Para una API de este tipo es la opción más productiva en Python moderno.

**¿Por qué Svelte y no React o Vue?**
> Svelte compila a JavaScript vanilla sin runtime, lo que lo hace muy liviano. Svelte 5 con runes es especialmente limpio para proyectos académicos porque la reactividad es explícita y fácil de leer.

**¿Qué pasaría si el historial crece mucho?**
> El archivo JSON actual no es ideal para millones de registros. El siguiente paso natural sería reemplazar `history_service.py` con una base de datos SQLite usando el mismo contrato de funciones — el resto del sistema no cambiaría.

**¿La contraseña se guarda en algún lado?**
> No. El campo `password` se recibe en el endpoint pero no se almacena ni se loguea. Está disponible como parámetro en el handler de almacenamiento para cuando se integren protocolos que requieran autenticación real.
