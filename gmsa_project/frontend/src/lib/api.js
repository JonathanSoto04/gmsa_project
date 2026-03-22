/**
 * lib/api.js
 * ----------
 * All communication with the FastAPI backend lives here.
 * Components never call `fetch` directly — they import from this module.
 * This makes it trivial to swap the backend URL, add auth headers,
 * or mock the API in tests.
 */

import { API_URL } from './config.js'

/**
 * Pings the backend to check whether it is reachable.
 * @returns {Promise<boolean>}
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
 * Fetches the backend configuration (max size, allowed extensions, protocols).
 * @returns {Promise<object>}
 */
export async function fetchConfig() {
  const res = await fetch(`${API_URL}/config`)
  if (!res.ok) throw new Error(`Config fetch failed: ${res.status}`)
  return res.json()
}

/**
 * Fetches all upload history records (newest first).
 * @returns {Promise<{total: number, items: Array}>}
 */
export async function fetchHistory() {
  const res = await fetch(`${API_URL}/history`)
  if (!res.ok) throw new Error(`History fetch failed: ${res.status}`)
  return res.json()
}

/**
 * Posts a file upload to the backend.
 * @param {FormData} formData
 * @returns {Promise<{ok: boolean, data: object}>}
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
 * Deletes all history records on the backend.
 * @returns {Promise<object>}
 */
export async function clearHistory() {
  const res = await fetch(`${API_URL}/history`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Clear history failed: ${res.status}`)
  return res.json()
}
