<script>
  import { onMount } from 'svelte'
  import {
    checkApiStatus,
    fetchConfig,
    fetchHistory,
    fetchStoredFiles,
  } from './lib/api.js'

  import Header from './components/Header.svelte'
  import StatsBar from './components/StatsBar.svelte'
  import ProtocolSelector from './components/ProtocolSelector.svelte'
  import UploadForm from './components/UploadForm.svelte'
  import HistoryTable from './components/HistoryTable.svelte'
  import FilesManager from './components/FilesManager.svelte'

  let apiOnline = $state(false)
  let protocol = $state('nfs')
  let history = $state([])
  let storedFiles = $state([])
  let fileWarnings = $state([])
  let maxFileSizeMb = $state(10)
  let allowedExtensions = $state([])
  let supportedProtocols = $state([])

  onMount(async () => {
    apiOnline = await checkApiStatus()

    if (!apiOnline) return

    const [config, hist, files] = await Promise.all([
      fetchConfig(),
      fetchHistory(),
      fetchStoredFiles(),
    ])

    maxFileSizeMb = config.max_file_size_mb ?? 10
    allowedExtensions = config.allowed_extensions ?? []
    supportedProtocols = config.supported_protocols ?? []
    history = hist.items ?? []
    storedFiles = files.items ?? []
    fileWarnings = files.warnings ?? []
  })

  async function reloadStoredFiles() {
    if (!apiOnline) return

    const files = await fetchStoredFiles()
    storedFiles = files.items ?? []
    fileWarnings = files.warnings ?? []
    return files
  }

  async function handleUploadSuccess(record) {
    history = [record, ...history]
    await reloadStoredFiles()
  }

  function handleHistoryCleared() {
    history = []
  }

  function handleFileDeleted(deletedFile) {
    storedFiles = storedFiles.filter((item) => item.path !== deletedFile.path)
  }
</script>

<Header {apiOnline} />

<main class="page-shell container-fluid px-4 py-5">
  <div class="page-header mb-5">
    <div class="page-header-chip mb-3">
      <i class="bi bi-diagram-3-fill me-2"></i>
      Dashboard local · Proyecto academico
    </div>
    <h1 class="page-title mb-2">Gestor Multiservicio<br />de Almacenamiento</h1>
    <p class="page-subtitle">
      Plataforma local para la carga de archivos mediante NFS, FTP, S3&nbsp;/&nbsp;MinIO y SMB,
      con validaciones, historial persistente y arquitectura preparada para integraciones reales.
    </p>
  </div>

  <StatsBar {history} />

  <div class="row g-4">
    <div class="col-xl-7">
      <div class="glass-panel p-4 p-lg-5">
        <div class="panel-heading mb-4">
          <div>
            <div class="section-title">Carga de archivos</div>
            <div class="section-subtitle">
              Selecciona un protocolo, envia un archivo y registra el resultado.
            </div>
          </div>

          <span class="protocol-badge-current">
            <i class="bi bi-broadcast me-1"></i>
            {protocol.toUpperCase()}
          </span>
        </div>

        <div class="mb-4">
          <ProtocolSelector
            selected={protocol}
            onselect={(selectedProtocol) => {
              protocol = selectedProtocol
            }}
          />
        </div>

        <hr class="panel-divider mb-4" />

        <UploadForm
          {protocol}
          {maxFileSizeMb}
          {allowedExtensions}
          onuploadSuccess={handleUploadSuccess}
        />
      </div>
    </div>

    <div class="col-xl-5">
      <div class="glass-panel p-4 p-lg-5 h-100">
        <HistoryTable {history} oncleared={handleHistoryCleared} />
      </div>
    </div>
  </div>

  <div class="row g-4 mt-1">
    <div class="col-12">
      <div class="glass-panel p-4 p-lg-5">
        <FilesManager
          files={storedFiles}
          supportedProtocols={supportedProtocols}
          initialWarnings={fileWarnings}
          ondeleted={handleFileDeleted}
          onrefresh={reloadStoredFiles}
        />
      </div>
    </div>
  </div>

  <footer class="page-footer mt-5">
    La capa de almacenamiento mantiene el historial separado del inventario local administrable.
  </footer>
</main>
