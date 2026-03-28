import { API_URL } from './config.js'

async function readJsonSafely(response) {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return null
  return response.json()
}

function buildApiError(data, fallback) {
  return new Error(data?.detail ?? data?.message ?? fallback)
}

export async function checkApiStatus() {
  try {
    const response = await fetch(`${API_URL}/`, {
      signal: AbortSignal.timeout(3000),
    })
    return response.ok
  } catch {
    return false
  }
}

export async function fetchConfig() {
  const response = await fetch(`${API_URL}/config`)
  const data = await readJsonSafely(response)
  if (!response.ok) {
    throw buildApiError(data, `Error al obtener la configuracion: ${response.status}`)
  }
  return data
}

export async function fetchHistory() {
  const response = await fetch(`${API_URL}/history`)
  const data = await readJsonSafely(response)
  if (!response.ok) {
    throw buildApiError(data, `Error al obtener el historial: ${response.status}`)
  }
  return data
}

export async function uploadFile(formData) {
  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  const data = await readJsonSafely(response)
  return { ok: response.ok, data }
}

export async function clearHistory() {
  const response = await fetch(`${API_URL}/history`, { method: 'DELETE' })
  const data = await readJsonSafely(response)
  if (!response.ok) {
    throw buildApiError(data, `Error al limpiar el historial: ${response.status}`)
  }
  return data
}

export async function fetchStoredFiles(protocol = '') {
  const url = new URL(`${API_URL}/files`)
  if (protocol) url.searchParams.set('protocol', protocol)

  const response = await fetch(url)
  const data = await readJsonSafely(response)
  if (!response.ok) {
    throw buildApiError(data, `Error al obtener los archivos: ${response.status}`)
  }
  return data
}

export async function deleteStoredFile(protocol, name) {
  const response = await fetch(`${API_URL}/files`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ protocol, name }),
  })

  const data = await readJsonSafely(response)
  if (!response.ok) {
    throw buildApiError(data, `Error al eliminar el archivo: ${response.status}`)
  }
  return data
}
