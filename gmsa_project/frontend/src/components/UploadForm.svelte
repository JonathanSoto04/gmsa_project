<script>
  import { uploadFile } from '../lib/api.js'

  /**
   * @type {{
   *   protocol: string,
   *   maxFileSizeMb: number,
   *   allowedExtensions: string[],
   *   onuploadSuccess: (record: object) => void
   * }}
   */
  let { protocol, maxFileSizeMb = 10, allowedExtensions = [], onuploadSuccess } = $props()

  let username = $state('')
  let password = $state('')
  let selectedFile = $state(null)
  let progress = $state(0)
  let loading = $state(false)
  let successMsg = $state('')
  let errorMsg = $state('')

  // Ref to the file input element so we can reset it after upload.
  let fileInputEl = $state(null)

  let formattedExtensions = $derived(
    allowedExtensions.map(e => e.replace('.', '').toUpperCase()).join(', ')
  )

  function handleFileChange(e) {
    selectedFile = e.target.files[0] ?? null
    successMsg = ''
    errorMsg = ''
  }

  function simulateProgress() {
    progress = 0
    const interval = setInterval(() => {
      if (progress < 90) progress += 10
      else clearInterval(interval)
    }, 120)
    return interval
  }

  async function handleUpload() {
    successMsg = ''
    errorMsg = ''

    if (!selectedFile) {
      errorMsg = 'Debes seleccionar un archivo antes de continuar.'
      return
    }

    const ext = `.${selectedFile.name.split('.').pop()?.toLowerCase() ?? ''}`
    if (!allowedExtensions.includes(ext)) {
      errorMsg = `Extensión '${ext}' no permitida. Tipos aceptados: ${formattedExtensions}.`
      return
    }

    if (selectedFile.size > maxFileSizeMb * 1024 * 1024) {
      errorMsg = `El archivo supera el límite de ${maxFileSizeMb} MB.`
      return
    }

    const formData = new FormData()
    formData.append('protocol', protocol)
    formData.append('username', username)
    formData.append('password', password)
    formData.append('file', selectedFile)

    loading = true
    const progressInterval = simulateProgress()

    try {
      const { ok, data } = await uploadFile(formData)

      clearInterval(progressInterval)
      progress = 100

      if (!ok) {
        errorMsg = data.detail ?? 'Ocurrió un error durante la subida.'
      } else {
        successMsg = data.message ?? 'Archivo subido correctamente.'
        // Reset form
        username = ''
        password = ''
        selectedFile = null
        if (fileInputEl) fileInputEl.value = ''
        onuploadSuccess?.(data.record)
      }
    } catch {
      clearInterval(progressInterval)
      errorMsg = 'No se pudo conectar con el backend. Verifica que la API esté en línea.'
    } finally {
      loading = false
      setTimeout(() => { progress = 0 }, 1800)
    }
  }
</script>

<div class="upload-form">

  <!-- Credentials -->
  <div class="row g-3 mb-4">
    <div class="col-md-6">
      <label class="form-label field-label">
        <i class="bi bi-person-fill me-1"></i> Usuario
      </label>
      <input
        type="text"
        class="form-control"
        bind:value={username}
        placeholder="Ej: admin, jonathan, storage_user"
        autocomplete="username"
      />
    </div>
    <div class="col-md-6">
      <label class="form-label field-label">
        <i class="bi bi-key-fill me-1"></i> Contraseña
      </label>
      <input
        type="password"
        class="form-control"
        bind:value={password}
        placeholder="Contraseña de acceso"
        autocomplete="current-password"
      />
    </div>
  </div>

  <!-- File input -->
  <div class="mb-4">
    <label class="form-label field-label">
      <i class="bi bi-file-earmark-arrow-up-fill me-1"></i> Archivo
    </label>
    <input
      type="file"
      class="form-control"
      bind:this={fileInputEl}
      onchange={handleFileChange}
    />
    <div class="field-hint mt-2">
      Formatos: {formattedExtensions} &nbsp;·&nbsp; Máximo: {maxFileSizeMb} MB
    </div>
  </div>

  <!-- Progress bar -->
  {#if progress > 0}
    <div class="mb-4">
      <div
        class="progress"
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          class="progress-bar progress-bar-striped progress-bar-animated"
          style={`width: ${progress}%`}
        >
          {progress < 100 ? `${progress}%` : 'Completado'}
        </div>
      </div>
    </div>
  {/if}

  <!-- Alerts -->
  {#if successMsg}
    <div class="alert-box alert-box--success mb-4">
      <i class="bi bi-check-circle-fill"></i>
      <span>{successMsg}</span>
    </div>
  {/if}

  {#if errorMsg}
    <div class="alert-box alert-box--error mb-4">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{errorMsg}</span>
    </div>
  {/if}

  <!-- Submit -->
  <button
    class="btn-upload w-100"
    onclick={handleUpload}
    disabled={loading}
    aria-busy={loading}
  >
    {#if loading}
      <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
      Subiendo archivo...
    {:else}
      <i class="bi bi-cloud-arrow-up-fill me-2"></i>
      Subir archivo
    {/if}
  </button>

</div>
