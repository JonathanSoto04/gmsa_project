/**
 * Archivo : lib/config.js
 * Descripción:
 *   Constantes de configuración globales del frontend.
 *
 *   Centraliza los valores que pueden variar según el entorno de despliegue.
 *   Para apuntar a un backend diferente (otro host, puerto o entorno),
 *   basta con modificar ``API_URL`` en este único archivo.
 *
 * Arquitectura:
 *   Todos los módulos que necesiten comunicarse con el backend deben
 *   importar ``API_URL`` desde aquí en lugar de definir la URL directamente.
 *   Esto evita la dispersión de valores de configuración por el código fuente.
 */

/** URL base del backend FastAPI. Modificar para apuntar a otro entorno. */
export const API_URL = 'http://127.0.0.1:8000'
