/**
 * Archivo : lib/api.js
 * Descripción:
 *   Módulo de comunicación con el backend FastAPI.
 *
 *   Centraliza todas las llamadas HTTP al servidor en un único lugar.
 *   Los componentes Svelte nunca invocan ``fetch`` directamente; en su
 *   lugar importan las funciones de este módulo. Esto facilita:
 *     - Cambiar la URL base del backend en un solo punto (config.js).
 *     - Añadir cabeceras de autenticación o interceptores de forma global.
 *     - Simular o reemplazar el backend en pruebas unitarias.
 *
 * Arquitectura:
 *   Depende de ``lib/config.js`` para obtener la URL base de la API.
 *   Es utilizado por ``App.svelte`` y los componentes ``UploadForm``
 *   e ``HistoryTable``.
 */

import { API_URL } from './config.js'

/**
 * Verifica si el backend está disponible realizando una petición GET a la raíz.
 *
 * Utiliza un timeout de 3 segundos para no bloquear la inicialización del
 * frontend si el servidor no responde.
 *
 * @returns {Promise<boolean>} ``true`` si la API responde con estado OK, ``false`` en caso contrario.
 */
export async function checkApiStatus() {
  try {
    const res = await fetch(`${API_URL}/`, {
      signal: AbortSignal.timeout(3000),
    })
    return res.ok
  } catch {
    return false
  }
}

/**
 * Obtiene la configuración pública del backend.
 *
 * El frontend utiliza estos datos para renderizar dinámicamente los
 * protocolos disponibles, limitar el tamaño del archivo antes de enviarlo
 * y mostrar los formatos aceptados al usuario.
 *
 * @returns {Promise<object>} Objeto con ``max_file_size_mb``, ``allowed_extensions`` y ``supported_protocols``.
 * @throws {Error} Si la respuesta del servidor no es exitosa.
 */
export async function fetchConfig() {
  const res = await fetch(`${API_URL}/config`)
  if (!res.ok) throw new Error(`Error al obtener la configuración: ${res.status}`)
  return res.json()
}

/**
 * Recupera todos los registros del historial de cargas desde el backend.
 *
 * Los registros se reciben ordenados del más reciente al más antiguo,
 * tal como los devuelve el endpoint ``GET /history``.
 *
 * @returns {Promise<{total: number, items: Array}>} Objeto con el total y la lista de registros.
 * @throws {Error} Si la respuesta del servidor no es exitosa.
 */
export async function fetchHistory() {
  const res = await fetch(`${API_URL}/history`)
  if (!res.ok) throw new Error(`Error al obtener el historial: ${res.status}`)
  return res.json()
}

/**
 * Envía un archivo al backend mediante una solicitud ``POST`` multipart/form-data.
 *
 * El ``FormData`` debe contener los campos ``protocol``, ``username``,
 * ``password`` y ``file``, que son los parámetros esperados por el
 * endpoint ``POST /upload``.
 *
 * @param {FormData} formData - Datos del formulario con el archivo y los metadatos.
 * @returns {Promise<{ok: boolean, data: object}>} Objeto con el estado HTTP y el cuerpo de la respuesta.
 */
export async function uploadFile(formData) {
  const res = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  })
  const data = await res.json()
  return { ok: res.ok, data }
}

/**
 * Elimina todos los registros del historial en el backend.
 *
 * Realiza una solicitud ``DELETE`` al endpoint ``/history``. La operación
 * es irreversible y no requiere parámetros adicionales.
 *
 * @returns {Promise<object>} Objeto de respuesta del servidor con confirmación de la operación.
 * @throws {Error} Si la respuesta del servidor no es exitosa.
 */
export async function clearHistory() {
  const res = await fetch(`${API_URL}/history`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Error al limpiar el historial: ${res.status}`)
  return res.json()
}
