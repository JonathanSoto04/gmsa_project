<script>
  import { onMount } from 'svelte'

  // URL base del backend FastAPI.
  const API_URL = 'http://127.0.0.1:8000'

  // Estado del formulario y la aplicación.
  let protocol = 'nfs'
  let username = ''
  let password = ''
  let selectedFile = null
  let loading = false
  let progress = 0
  let message = ''
  let error = ''
  let history = []
  let maxFileSizeMb = 10
  let allowedExtensions = []

  // Tarjetas visibles en el dashboard.
  const protocolCards = [
    {
      key: 'nfs',
      title: 'NFS',
      desc: 'Carga orientada a almacenamiento compartido en red para entornos Linux o rutas montadas.'
    },
    {
      key: 'ftp',
      title: 'FTP',
      desc: 'Transferencia tradicional de archivos usando un servidor FTP y credenciales del usuario.'
    },
    {
      key: 'sftp',
      title: 'SFTP',
      desc: 'Transferencia segura sobre SSH, ideal para entornos que requieren autenticación protegida.'
    },
    {
      key: 's3',
      title: 'S3 / MinIO',
      desc: 'Almacenamiento tipo objeto compatible con Amazon S3 para integraciones modernas.'
    },
    {
      key: 'smb',
      title: 'SMB',
      desc: 'Carga hacia carpetas compartidas en entornos Windows o recursos de red empresariales.'
    }
  ]

  /**
   * Carga parámetros configurables desde el backend:
   * - tamaño máximo permitido
   * - extensiones permitidas
   */
  async function fetchConfig() {
    try {
      const response = await fetch(`${API_URL}/config`)
      const data = await response.json()
      maxFileSizeMb = data.max_file_size_mb || 10
      allowedExtensions = data.allowed_extensions || []
    } catch (err) {
      console.error('No se pudo cargar la configuración del backend.', err)
    }
  }

  /**
   * Recupera el historial de cargas para mostrarlo en la tabla lateral.
   */
  async function fetchHistory() {
    try {
      const response = await fetch(`${API_URL}/history`)
      const data = await response.json()
      history = data.items || []
    } catch (err) {
      console.error('No se pudo cargar el historial.', err)
    }
  }

  /**
   * Actualiza el archivo seleccionado desde el input file.
   */
  function handleFileChange(event) {
    selectedFile = event.target.files[0]
    message = ''
    error = ''
  }

  /**
   * Barra de progreso visual para mejorar UX.
   * En esta versión es simulada hasta que el backend responde.
   */
  function simulateProgress() {
    progress = 0
    const interval = setInterval(() => {
      if (progress < 92) {
        progress += 8
      } else {
        clearInterval(interval)
      }
    }, 140)
    return interval
  }

  /**
   * Convierte la lista de extensiones permitidas del backend en un formato
   * más amigable para mostrar en pantalla.
   */
  function formatExtensions(list) {
    return list
      .map((item) => item.replace('.', '').toUpperCase())
      .join(', ')
  }

  /**
   * Realiza la carga del archivo al backend.
   * Flujo:
   * 1. Validar archivo seleccionado.
   * 2. Validar extensión y tamaño.
   * 3. Enviar multipart/form-data.
   * 4. Mostrar respuesta y refrescar historial.
   */
  async function uploadFile() {
    error = ''
    message = ''

    if (!selectedFile) {
      error = 'Debes seleccionar un archivo antes de continuar.'
      return
    }

    const extension = `.${selectedFile.name.split('.').pop()?.toLowerCase() || ''}`
    if (!allowedExtensions.includes(extension)) {
      error = `Tipo de archivo no permitido. Extensión detectada: ${extension}`
      return
    }

    if (selectedFile.size > maxFileSizeMb * 1024 * 1024) {
      error = `El archivo supera el límite de ${maxFileSizeMb} MB.`
      return
    }

    const formData = new FormData()
    formData.append('protocol', protocol)
    formData.append('username', username)
    formData.append('password', password)
    formData.append('file', selectedFile)

    loading = true
    progress = 0
    const interval = simulateProgress()

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      clearInterval(interval)
      progress = 100

      if (!response.ok) {
        error = data.detail || 'Ocurrió un error durante la subida.'
      } else {
        message = data.message || 'Archivo subido correctamente.'
        username = ''
        password = ''
        selectedFile = null
        document.getElementById('fileInput').value = ''
        await fetchHistory()
      }
    } catch (err) {
      clearInterval(interval)
      error = 'No se pudo conectar con el backend FastAPI.'
      console.error(err)
    } finally {
      loading = false
      setTimeout(() => {
        progress = 0
      }, 1500)
    }
  }

  // Métricas derivadas mostradas arriba del dashboard.
  $: totalUploads = history.length
  $: successUploads = history.filter((item) => item.status === 'Éxito').length
  $: errorUploads = history.filter((item) => item.status === 'Error').length
  $: recentProtocol = history.length > 0 ? history[0].protocol : 'Sin registros'

  onMount(async () => {
    await fetchConfig()
    await fetchHistory()
  })
</script>

<div class="page-shell container py-4 py-lg-5">
  <div class="mb-4 mb-lg-5">
    <div class="title-chip mb-3">Dashboard local · FastAPI + Svelte + Bootstrap</div>
    <h1 class="hero-title mb-3">Gestor Multiservicio de Almacenamiento</h1>
    <p class="hero-subtitle mb-0">
      Plataforma local para gestionar la carga de archivos mediante NFS, FTP, SFTP, S3 / MinIO y SMB,
      con validaciones, historial persistente, control de errores y una interfaz tipo dashboard admin.
    </p>
  </div>

  <div class="row g-3 g-lg-4 mb-4 mb-lg-5">
    <div class="col-md-6 col-xl-3">
      <div class="glass-panel stat-card">
        <div class="stat-label mb-2">Total de cargas registradas</div>
        <div class="stat-value">{totalUploads}</div>
      </div>
    </div>
    <div class="col-md-6 col-xl-3">
      <div class="glass-panel stat-card">
        <div class="stat-label mb-2">Operaciones exitosas</div>
        <div class="stat-value text-success">{successUploads}</div>
      </div>
    </div>
    <div class="col-md-6 col-xl-3">
      <div class="glass-panel stat-card">
        <div class="stat-label mb-2">Errores detectados</div>
        <div class="stat-value text-danger">{errorUploads}</div>
      </div>
    </div>
    <div class="col-md-6 col-xl-3">
      <div class="glass-panel stat-card">
        <div class="stat-label mb-2">Último protocolo usado</div>
        <div class="stat-value" style="font-size: 1.45rem;">{recentProtocol}</div>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-xl-7">
      <div class="glass-panel p-4 p-lg-4">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-3 mb-4">
          <div>
            <div class="section-heading">Carga de archivos</div>
            <div class="small-muted">Selecciona un protocolo, ingresa credenciales y envía el archivo.</div>
          </div>
          <div class="badge-soft">Protocolo actual: {protocol.toUpperCase()}</div>
        </div>

        <div class="row g-3 mb-4">
          {#each protocolCards as item}
            <div class="col-md-6">
              <button
                type="button"
                class={`protocol-card w-100 text-start ${protocol === item.key ? 'active' : ''}`}
                on:click={() => (protocol = item.key)}
              >
                <div class="protocol-title mb-1">{item.title}</div>
                <div class="protocol-desc">{item.desc}</div>
              </button>
            </div>
          {/each}
        </div>

        <div class="row g-3">
          <div class="col-md-6">
            <label class="label-title">Usuario</label>
            <input
              type="text"
              class="form-control"
              bind:value={username}
              placeholder="Ej: admin, jonathan, storage_user"
            />
          </div>

          <div class="col-md-6">
            <label class="label-title">Contraseña</label>
            <input
              type="password"
              class="form-control"
              bind:value={password}
              placeholder="Ingrese la contraseña"
            />
          </div>

          <div class="col-12">
            <label class="label-title">Archivo</label>
            <input id="fileInput" type="file" class="form-control" on:change={handleFileChange} />
            <div class="helper-text mt-2">
              Formatos permitidos: {formatExtensions(allowedExtensions)} · Tamaño máximo: {maxFileSizeMb} MB.
            </div>
          </div>
        </div>

        {#if progress > 0}
          <div class="mt-4">
            <div class="progress" role="progressbar" aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100">
              <div class="progress-bar progress-bar-striped progress-bar-animated" style={`width: ${progress}%`}>
                {progress}%
              </div>
            </div>
          </div>
        {/if}

        {#if message}
          <div class="alert alert-success mt-4 mb-0">{message}</div>
        {/if}

        {#if error}
          <div class="alert alert-danger mt-4 mb-0">{error}</div>
        {/if}

        <button class="btn btn-gradient w-100 mt-4" on:click={uploadFile} disabled={loading}>
          {#if loading}
            Subiendo archivo...
          {:else}
            Subir archivo al sistema
          {/if}
        </button>
      </div>
    </div>

    <div class="col-xl-5">
      <div class="glass-panel p-4 h-100">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <div>
            <div class="section-heading">Historial de cargas</div>
            <div class="small-muted">Registros persistidos en un JSON local del backend.</div>
          </div>
          <div class="badge-soft">{history.length} registros</div>
        </div>

        {#if history.length === 0}
          <div class="panel-soft p-4 text-center">
            <div class="fw-semibold mb-2">Aún no hay registros</div>
            <div class="small-muted">Cuando subas archivos, aquí verás su fecha, protocolo y estado.</div>
          </div>
        {:else}
          <div class="table-shell">
            <table class="table table-dark table-striped align-middle">
              <thead>
                <tr>
                  <th>Archivo</th>
                  <th>Protocolo</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {#each history as item}
                  <tr>
                    <td>
                      <div class="fw-semibold">{item.filename}</div>
                      <div class="small-muted">{item.uploaded_at}</div>
                    </td>
                    <td>{item.protocol}</td>
                    <td>
                      <span class={`badge ${item.status === 'Éxito' ? 'text-bg-success' : 'text-bg-danger'}`}>
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
    </div>
  </div>

  <div class="footer-note mt-4 mt-lg-5">
    Proyecto base preparado para que la capa de conexión real por protocolo sea integrada posteriormente
    sin modificar la experiencia visual del sistema.
  </div>
</div>
