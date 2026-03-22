<script>
  import { onMount } from 'svelte'
  import { checkApiStatus, fetchConfig, fetchHistory } from './lib/api.js'

  import Header from './components/Header.svelte'
  import StatsBar from './components/StatsBar.svelte'
  import ProtocolSelector from './components/ProtocolSelector.svelte'
  import UploadForm from './components/UploadForm.svelte'
  import HistoryTable from './components/HistoryTable.svelte'

  // ---- Shared state --------------------------------------------------------
  let apiOnline        = $state(false)
  let protocol         = $state('nfs')
  let history          = $state([])
  let maxFileSizeMb    = $state(10)
  let allowedExtensions = $state([])

  // ---- Initialization ------------------------------------------------------
  onMount(async () => {
    apiOnline = await checkApiStatus()

    if (apiOnline) {
      const [config, hist] = await Promise.all([fetchConfig(), fetchHistory()])
      maxFileSizeMb     = config.max_file_size_mb ?? 10
      allowedExtensions = config.allowed_extensions ?? []
      history           = hist.items ?? []
    }
  })

  // ---- Event handlers ------------------------------------------------------

  /** Called when a file is successfully uploaded. Prepends the new record. */
  function handleUploadSuccess(record) {
    history = [record, ...history]
  }

  /** Called when the user clears the history. */
  async function handleHistoryCleared() {
    history = []
  }
</script>

<Header {apiOnline} />

<main class="page-shell container-fluid px-4 py-5">

  <!-- Page header -->
  <div class="page-header mb-5">
    <div class="page-header-chip mb-3">
      <i class="bi bi-diagram-3-fill me-2"></i>
      Dashboard local · Proyecto académico
    </div>
    <h1 class="page-title mb-2">Gestor Multiservicio<br />de Almacenamiento</h1>
    <p class="page-subtitle">
      Plataforma local para la carga de archivos mediante NFS, FTP, SFTP, S3&nbsp;/&nbsp;MinIO y SMB,
      con validaciones, historial persistente y arquitectura preparada para integraciones reales.
    </p>
  </div>

  <!-- Stats row -->
  <StatsBar {history} />

  <!-- Main grid: upload panel + history panel -->
  <div class="row g-4">

    <!-- Upload panel -->
    <div class="col-xl-7">
      <div class="glass-panel p-4 p-lg-5">

        <div class="panel-heading mb-4">
          <div>
            <div class="section-title">Carga de archivos</div>
            <div class="section-subtitle">
              Selecciona un protocolo, ingresa credenciales y envía el archivo.
            </div>
          </div>
          <span class="protocol-badge-current">
            <i class="bi bi-broadcast me-1"></i>
            {protocol.toUpperCase()}
          </span>
        </div>

        <!-- Protocol selector -->
        <div class="mb-4">
          <ProtocolSelector
            selected={protocol}
            onselect={(p) => { protocol = p }}
          />
        </div>

        <hr class="panel-divider mb-4" />

        <!-- Upload form -->
        <UploadForm
          {protocol}
          {maxFileSizeMb}
          {allowedExtensions}
          onuploadSuccess={handleUploadSuccess}
        />

      </div>
    </div>

    <!-- History panel -->
    <div class="col-xl-5">
      <div class="glass-panel p-4 p-lg-5 h-100">
        <HistoryTable {history} oncleared={handleHistoryCleared} />
      </div>
    </div>

  </div>

  <footer class="page-footer mt-5">
    La capa de almacenamiento está preparada para integrar protocolos reales sin modificar
    la interfaz ni el flujo de la API.
  </footer>

</main>
