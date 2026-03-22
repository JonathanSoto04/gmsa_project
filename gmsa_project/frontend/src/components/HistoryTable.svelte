<!--
  Archivo : components/HistoryTable.svelte
  Descripción:
    Componente que renderiza el historial de cargas de archivos en formato
    de tabla y permite al usuario eliminarlo completamente.

    Muestra los registros con sus metadatos: nombre del archivo, protocolo
    utilizado, tamaño, usuario y estado (éxito o error). Cuando el historial
    está vacío presenta un estado visual de «sin registros». La acción de
    limpiar solicita confirmación antes de invocar al backend.

  Props:
    · history   {Array}    — lista de registros del historial. Cada elemento
                             debe contener: ``id``, ``filename``, ``uploaded_at``,
                             ``protocol``, ``size_kb``, ``username`` y ``status``.
    · oncleared {Function} — callback invocado sin argumentos cuando el historial
                             se elimina exitosamente, para que el padre actualice
                             su estado.

  Estado local:
    · clearing   {boolean} — indica si la operación de limpieza está en progreso.
                             Desactiva el botón para evitar doble envío.
    · clearError {string}  — mensaje de error mostrado si la limpieza falla.

  API consumida:
    · DELETE /history  (clearHistory)
-->

<script>
  import { clearHistory } from '../lib/api.js'

  /**
   * Props del componente HistoryTable.
   * @type {{
   *   history: Array,
   *   oncleared: () => void
   * }}
   */
  let { history = [], oncleared } = $props()

  /** Indica si la operación de limpieza está en curso. */
  let clearing = $state(false)

  /** Mensaje de error mostrado si la llamada a la API falla. */
  let clearError = $state('')

  /**
   * Maneja la acción de limpiar el historial.
   * Solicita confirmación al usuario antes de proceder con la operación
   * irreversible de eliminación en el backend.
   */
  async function handleClear() {
    // Confirmación explícita del usuario antes de una acción destructiva.
    if (!confirm('¿Eliminar todo el historial? Esta acción no se puede deshacer.')) return
    clearing = true
    clearError = ''
    try {
      await clearHistory()
      // Notificar al componente padre para que actualice su estado local.
      oncleared?.()
    } catch {
      clearError = 'No se pudo limpiar el historial.'
    } finally {
      clearing = false
    }
  }

  /**
   * Formatea un tamaño en kilobytes a una representación legible.
   * Utiliza MB si el valor supera 1024 KB, de lo contrario muestra KB.
   *
   * @param {number} kb - Tamaño en kilobytes.
   * @returns {string} Cadena formateada con unidad (p. ej., «2.5 MB» o «512.0 KB»).
   */
  function formatSize(kb) {
    if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
    return `${kb.toFixed(1)} KB`
  }
</script>

<div class="history-panel">

  <!-- Encabezado del panel con contador de registros y botón de limpieza -->
  <div class="history-header">
    <div>
      <div class="section-title">Historial de cargas</div>
      <div class="section-subtitle">Registros persistidos en JSON local</div>
    </div>
    <div class="history-header-right">
      <!-- Contador de registros actuales -->
      <span class="count-badge">{history.length} registros</span>
      <!-- Botón de limpieza: solo visible cuando hay registros -->
      {#if history.length > 0}
        <button
          class="btn-clear"
          onclick={handleClear}
          disabled={clearing}
          title="Limpiar historial"
        >
          <i class="bi bi-trash3-fill"></i>
        </button>
      {/if}
    </div>
  </div>

  <!-- Mensaje de error si la operación de limpieza falla -->
  {#if clearError}
    <div class="alert-box alert-box--error mb-3">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{clearError}</span>
    </div>
  {/if}

  <!-- Vista condicional: tabla de registros o estado vacío -->
  {#if history.length === 0}
    <!-- Estado vacío: se muestra cuando no hay registros en el historial -->
    <div class="empty-state">
      <div class="empty-state-icon">
        <i class="bi bi-inbox"></i>
      </div>
      <div class="empty-state-title">Sin registros</div>
      <div class="empty-state-desc">
        Cuando subas archivos, aparecerán aquí con protocolo, tamaño y estado.
      </div>
    </div>
  {:else}
    <!-- Tabla de registros: se itera con ``item.id`` como clave para optimizar actualizaciones del DOM -->
    <div class="table-shell">
      <table class="table table-dark table-striped align-middle mb-0">
        <thead>
          <tr>
            <th>Archivo</th>
            <th>Protocolo</th>
            <th>Tamaño</th>
            <th>Usuario</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {#each history as item (item.id)}
            <tr>
              <!-- Columna: nombre del archivo y fecha de carga -->
              <td>
                <div class="file-name">{item.filename}</div>
                <div class="file-date">{item.uploaded_at}</div>
              </td>
              <!-- Columna: badge con el nombre del protocolo -->
              <td>
                <span class="proto-badge">{item.protocol}</span>
              </td>
              <!-- Columna: tamaño formateado -->
              <td class="text-muted-sm">{formatSize(item.size_kb)}</td>
              <!-- Columna: nombre del usuario -->
              <td class="text-muted-sm">{item.username}</td>
              <!-- Columna: badge de estado con icono diferenciado por resultado -->
              <td>
                <span class={`status-badge ${item.status === 'Éxito' ? 'status-badge--ok' : 'status-badge--err'}`}>
                  {#if item.status === 'Éxito'}
                    <i class="bi bi-check-lg"></i>
                  {:else}
                    <i class="bi bi-x-lg"></i>
                  {/if}
                  {item.status}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

</div>
