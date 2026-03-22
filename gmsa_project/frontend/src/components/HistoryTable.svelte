<script>
  import { clearHistory } from '../lib/api.js'

  /**
   * @type {{
   *   history: Array,
   *   oncleared: () => void
   * }}
   */
  let { history = [], oncleared } = $props()

  let clearing = $state(false)
  let clearError = $state('')

  async function handleClear() {
    if (!confirm('¿Eliminar todo el historial? Esta acción no se puede deshacer.')) return
    clearing = true
    clearError = ''
    try {
      await clearHistory()
      oncleared?.()
    } catch {
      clearError = 'No se pudo limpiar el historial.'
    } finally {
      clearing = false
    }
  }

  function formatSize(kb) {
    if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
    return `${kb.toFixed(1)} KB`
  }
</script>

<div class="history-panel">

  <!-- Panel header -->
  <div class="history-header">
    <div>
      <div class="section-title">Historial de cargas</div>
      <div class="section-subtitle">Registros persistidos en JSON local</div>
    </div>
    <div class="history-header-right">
      <span class="count-badge">{history.length} registros</span>
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

  {#if clearError}
    <div class="alert-box alert-box--error mb-3">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{clearError}</span>
    </div>
  {/if}

  <!-- Table or empty state -->
  {#if history.length === 0}
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
              <td>
                <div class="file-name">{item.filename}</div>
                <div class="file-date">{item.uploaded_at}</div>
              </td>
              <td>
                <span class="proto-badge">{item.protocol}</span>
              </td>
              <td class="text-muted-sm">{formatSize(item.size_kb)}</td>
              <td class="text-muted-sm">{item.username}</td>
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
