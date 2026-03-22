<!--
  Archivo : App.svelte
  Descripción:
    Componente raíz de la aplicación. Actúa como orquestador principal:
    gestiona el estado global compartido, inicializa la comunicación con el
    backend al montarse y coordina la comunicación entre componentes hijos
    mediante props y callbacks.

  Estado gestionado:
    · apiOnline         — indica si el backend está accesible.
    · protocol          — protocolo de almacenamiento actualmente seleccionado.
    · history           — lista de registros de cargas del historial.
    · maxFileSizeMb     — límite de tamaño de archivo obtenido del backend.
    · allowedExtensions — extensiones permitidas obtenidas del backend.

  Inicialización (onMount):
    Al montarse, verifica el estado de la API y, si está en línea, carga
    en paralelo la configuración y el historial inicial para minimizar
    el tiempo de carga percibido por el usuario.

  Componentes hijos:
    · Header           — barra superior con nombre del proyecto y estado de la API.
    · StatsBar         — tarjetas con estadísticas derivadas del historial.
    · ProtocolSelector — selector visual del protocolo de almacenamiento.
    · UploadForm       — formulario de carga de archivos.
    · HistoryTable     — tabla con el historial de cargas y opción de limpieza.

  API consumida:
    · GET /           (checkApiStatus)
    · GET /config     (fetchConfig)
    · GET /history    (fetchHistory)
-->

<script>
  import { onMount } from 'svelte'
  import { checkApiStatus, fetchConfig, fetchHistory } from './lib/api.js'

  import Header from './components/Header.svelte'
  import StatsBar from './components/StatsBar.svelte'
  import ProtocolSelector from './components/ProtocolSelector.svelte'
  import UploadForm from './components/UploadForm.svelte'
  import HistoryTable from './components/HistoryTable.svelte'

  // ---------------------------------------------------------------------------
  // Estado global compartido entre componentes hijos
  // ---------------------------------------------------------------------------

  /** Indica si el backend FastAPI está accesible. Controla el indicador de estado en el Header. */
  let apiOnline        = $state(false)

  /** Protocolo de almacenamiento actualmente seleccionado por el usuario. */
  let protocol         = $state('nfs')

  /** Lista completa de registros del historial de cargas (del más reciente al más antiguo). */
  let history          = $state([])

  /** Límite de tamaño de archivo en MB, obtenido dinámicamente del backend. */
  let maxFileSizeMb    = $state(10)

  /** Lista de extensiones de archivo permitidas, obtenida dinámicamente del backend. */
  let allowedExtensions = $state([])

  // ---------------------------------------------------------------------------
  // Inicialización al montar el componente
  // ---------------------------------------------------------------------------

  /**
   * Al montarse, verifica si la API está en línea. Si lo está, obtiene en
   * paralelo la configuración y el historial inicial para reducir la latencia
   * de carga. Los valores de configuración provienen del backend para evitar
   * duplicación de lógica entre frontend y servidor.
   */
  onMount(async () => {
    apiOnline = await checkApiStatus()

    if (apiOnline) {
      // Carga en paralelo para minimizar el tiempo de inicialización.
      const [config, hist] = await Promise.all([fetchConfig(), fetchHistory()])
      maxFileSizeMb     = config.max_file_size_mb ?? 10
      allowedExtensions = config.allowed_extensions ?? []
      history           = hist.items ?? []
    }
  })

  // ---------------------------------------------------------------------------
  // Manejadores de eventos de componentes hijos
  // ---------------------------------------------------------------------------

  /**
   * Manejador invocado por ``UploadForm`` cuando una carga se completa con éxito.
   * Agrega el nuevo registro al inicio del historial (más reciente primero)
   * sin necesidad de recargar toda la lista desde el servidor.
   *
   * @param {object} record - Registro de historial devuelto por el backend.
   */
  function handleUploadSuccess(record) {
    history = [record, ...history]
  }

  /**
   * Manejador invocado por ``HistoryTable`` cuando el usuario limpia el historial.
   * Vacía la lista local de registros para reflejar el estado del servidor.
   */
  async function handleHistoryCleared() {
    history = []
  }
</script>

<!-- Barra de navegación superior con estado de la API -->
<Header {apiOnline} />

<main class="page-shell container-fluid px-4 py-5">

  <!-- Encabezado de la página con título y descripción del proyecto -->
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

  <!-- Barra de estadísticas derivadas del historial actual -->
  <StatsBar {history} />

  <!-- Cuadrícula principal: panel de carga (izquierda) + panel de historial (derecha) -->
  <div class="row g-4">

    <!-- Panel de carga de archivos -->
    <div class="col-xl-7">
      <div class="glass-panel p-4 p-lg-5">

        <div class="panel-heading mb-4">
          <div>
            <div class="section-title">Carga de archivos</div>
            <div class="section-subtitle">
              Selecciona un protocolo, ingresa credenciales y envía el archivo.
            </div>
          </div>
          <!-- Indicador del protocolo activo -->
          <span class="protocol-badge-current">
            <i class="bi bi-broadcast me-1"></i>
            {protocol.toUpperCase()}
          </span>
        </div>

        <!-- Selector de protocolo de almacenamiento -->
        <div class="mb-4">
          <ProtocolSelector
            selected={protocol}
            onselect={(p) => { protocol = p }}
          />
        </div>

        <hr class="panel-divider mb-4" />

        <!-- Formulario de carga; recibe el protocolo activo y los límites de validación -->
        <UploadForm
          {protocol}
          {maxFileSizeMb}
          {allowedExtensions}
          onuploadSuccess={handleUploadSuccess}
        />

      </div>
    </div>

    <!-- Panel del historial de cargas -->
    <div class="col-xl-5">
      <div class="glass-panel p-4 p-lg-5 h-100">
        <HistoryTable {history} oncleared={handleHistoryCleared} />
      </div>
    </div>

  </div>

  <!-- Pie de página informativo -->
  <footer class="page-footer mt-5">
    La capa de almacenamiento está preparada para integrar protocolos reales sin modificar
    la interfaz ni el flujo de la API.
  </footer>

</main>
