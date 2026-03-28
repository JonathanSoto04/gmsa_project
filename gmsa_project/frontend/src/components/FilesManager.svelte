<script>
  import { deleteStoredFile } from '../lib/api.js'

  let {
    files = [],
    supportedProtocols = [],
    initialWarnings = [],
    ondeleted,
    onrefresh,
  } = $props()

  let selectedProtocol = $state('all')
  let deletingKey = $state('')
  let refreshing = $state(false)
  let successMsg = $state('')
  let warningMsg = $state('')
  let errorMsg = $state('')
  let listWarningMsg = $state('')

  let protocolOptions = $derived(
    supportedProtocols.length > 0 ? supportedProtocols : ['ftp', 'nfs', 's3', 'smb']
  )

  let visibleFiles = $derived(
    selectedProtocol === 'all'
      ? files
      : files.filter((item) => item.protocol === selectedProtocol)
  )

  $effect(() => {
    if (!refreshing && !warningMsg && !errorMsg) {
      listWarningMsg = initialWarnings.join(' | ')
    }
  })

  function formatSize(bytes) {
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${bytes} B`
  }

  function formatDate(value) {
    if (!value) return '-'

    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value

    return date.toLocaleString('es-CO', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  async function handleRefresh() {
    if (!onrefresh) return

    refreshing = true
    successMsg = ''
    warningMsg = ''
    errorMsg = ''
    listWarningMsg = ''

    try {
      const result = await onrefresh()
      listWarningMsg = result?.warnings?.join(' | ') ?? ''
    } catch (error) {
      errorMsg = error?.message ?? 'No se pudo actualizar la lista de archivos.'
    } finally {
      refreshing = false
    }
  }

  async function handleDelete(item) {
    const confirmed = confirm(
      `¿Eliminar "${item.name}" del protocolo ${item.protocol.toUpperCase()}? Esta accion no se puede deshacer.`
    )

    if (!confirmed) return

    deletingKey = item.path
    successMsg = ''
    warningMsg = ''
    errorMsg = ''
    listWarningMsg = ''

    try {
      const response = await deleteStoredFile(item.protocol, item.name)

      if (response.remote_deleted === false) {
        warningMsg = response.warning
          ? `${response.message} Detalle: ${response.warning}`
          : response.message
        const refreshResult = await onrefresh?.()
        listWarningMsg = refreshResult?.warnings?.join(' | ') ?? ''
      } else {
        successMsg = response.message ?? 'Archivo eliminado correctamente.'
        ondeleted?.(response.deleted ?? item)
      }
    } catch (error) {
      errorMsg = error?.message ?? 'No se pudo eliminar el archivo.'
    } finally {
      deletingKey = ''
    }
  }
</script>

<div class="files-manager">
  <div class="files-header">
    <div>
      <div class="section-title">Archivos almacenados</div>
      <div class="section-subtitle">
        Archivos reales consultados desde cada protocolo remoto
      </div>
    </div>

    <div class="files-header-right">
      <span class="count-badge">{visibleFiles.length} visibles</span>
      <button
        class="btn-refresh"
        type="button"
        onclick={handleRefresh}
        disabled={refreshing}
        title="Actualizar lista"
      >
        {#if refreshing}
          <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        {:else}
          <i class="bi bi-arrow-clockwise"></i>
        {/if}
      </button>
    </div>
  </div>

  <div class="files-toolbar">
    <div class="files-filter">
      <label class="form-label field-label mb-2" for="stored-files-filter">
        <i class="bi bi-funnel-fill me-1"></i>
        Filtrar por protocolo
      </label>
      <select
        id="stored-files-filter"
        class="form-select"
        bind:value={selectedProtocol}
      >
        <option value="all">Todos los protocolos</option>
        {#each protocolOptions as protocol}
          <option value={protocol}>{protocol.toUpperCase()}</option>
        {/each}
      </select>
    </div>
  </div>

  {#if successMsg}
    <div class="alert-box alert-box--success mb-3">
      <i class="bi bi-check-circle-fill"></i>
      <span>{successMsg}</span>
    </div>
  {/if}

  {#if warningMsg}
    <div class="alert-box alert-box--warning mb-3">
      <i class="bi bi-exclamation-circle-fill"></i>
      <span>{warningMsg}</span>
    </div>
  {/if}

  {#if listWarningMsg}
    <div class="alert-box alert-box--warning mb-3">
      <i class="bi bi-wifi-off"></i>
      <span>{listWarningMsg}</span>
    </div>
  {/if}

  {#if errorMsg}
    <div class="alert-box alert-box--error mb-3">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{errorMsg}</span>
    </div>
  {/if}

  {#if visibleFiles.length === 0}
    <div class="empty-state files-empty-state">
      <div class="empty-state-icon">
        <i class="bi bi-folder2-open"></i>
      </div>
      <div class="empty-state-title">Sin archivos en esta vista</div>
      <div class="empty-state-desc">
        Si el protocolo remoto tiene archivos accesibles, apareceran aqui para administrarlos.
      </div>
    </div>
  {:else}
    <div class="table-shell table-shell--files">
      <table class="table table-dark table-striped align-middle mb-0">
        <thead>
          <tr>
            <th>Archivo</th>
            <th>Protocolo</th>
            <th>Tamano</th>
            <th>Ruta remota</th>
            <th>Modificado</th>
            <th class="text-end">Accion</th>
          </tr>
        </thead>
        <tbody>
          {#each visibleFiles as item (item.protocol + ':' + item.name)}
            <tr>
              <td>
                <div class="file-name">{item.name}</div>
                <div class="file-date">Referencia remota</div>
              </td>
              <td>
                <span class="proto-badge">{item.protocol.toUpperCase()}</span>
              </td>
              <td class="text-muted-sm">{formatSize(item.size)}</td>
              <td>
                <code class="file-path">{item.path}</code>
              </td>
              <td class="text-muted-sm">{formatDate(item.modified_at)}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn-delete-file"
                  onclick={() => handleDelete(item)}
                  disabled={deletingKey === item.path}
                >
                  {#if deletingKey === item.path}
                    <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                    Eliminando...
                  {:else}
                    <i class="bi bi-trash3-fill me-2"></i>
                    Eliminar
                  {/if}
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
