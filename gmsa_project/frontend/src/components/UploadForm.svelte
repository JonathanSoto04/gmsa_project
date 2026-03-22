<!--
  Archivo : components/UploadForm.svelte
  Descripción:
    Componente de formulario para la carga de archivos al backend.

    Permite al usuario ingresar credenciales (usuario y contraseña), seleccionar
    un archivo del sistema y enviarlo al protocolo de almacenamiento activo.
    Incluye validación en el cliente (extensión y tamaño) antes de realizar
    la llamada a la API, una barra de progreso animada durante la subida y
    mensajes de retroalimentación según el resultado de la operación.

  Props:
    · protocol          {string}   — protocolo de almacenamiento activo, seleccionado
                                     en ``ProtocolSelector``.
    · maxFileSizeMb     {number}   — límite de tamaño del archivo en MB (obtenido del backend).
    · allowedExtensions {string[]} — lista de extensiones de archivo permitidas (obtenida del backend).
    · onuploadSuccess   {Function} — callback invocado con el registro de historial
                                     cuando la carga se completa con éxito.

  Estado local:
    · username      — valor del campo de texto «Usuario».
    · password      — valor del campo de contraseña.
    · selectedFile  — objeto ``File`` seleccionado por el usuario, o ``null``.
    · progress      — porcentaje de progreso simulado de la barra de carga (0–100).
    · loading       — indica si la subida está en curso; desactiva el botón de envío.
    · successMsg    — mensaje de éxito mostrado tras una carga exitosa.
    · errorMsg      — mensaje de error mostrado si la validación o la API fallan.
    · fileInputEl   — referencia al elemento ``<input type="file">`` para resetearlo
                      tras una carga exitosa sin remontar el componente.

  API consumida:
    · POST /upload  (uploadFile)
-->

<script>
  import { uploadFile } from '../lib/api.js'

  /**
   * Props del componente UploadForm.
   * @type {{
   *   protocol: string,
   *   maxFileSizeMb: number,
   *   allowedExtensions: string[],
   *   onuploadSuccess: (record: object) => void
   * }}
   */
  let { protocol, maxFileSizeMb = 10, allowedExtensions = [], onuploadSuccess } = $props()

  // ---------------------------------------------------------------------------
  // Estado local del formulario
  // ---------------------------------------------------------------------------

  let username     = $state('')
  let password     = $state('')
  let selectedFile = $state(null)
  let progress     = $state(0)
  let loading      = $state(false)
  let successMsg   = $state('')
  let errorMsg     = $state('')

  /** Referencia al elemento input de tipo file para poder resetearlo tras la carga. */
  let fileInputEl  = $state(null)

  /**
   * Lista de extensiones formateadas para mostrar en el campo de ayuda.
   * Se transforman eliminando el punto y convirtiéndolas a mayúsculas.
   * Ejemplo: [".pdf", ".jpg"] → "PDF, JPG"
   */
  let formattedExtensions = $derived(
    allowedExtensions.map(e => e.replace('.', '').toUpperCase()).join(', ')
  )

  // ---------------------------------------------------------------------------
  // Manejadores de eventos
  // ---------------------------------------------------------------------------

  /**
   * Se invoca cuando el usuario selecciona un archivo en el input.
   * Actualiza el estado ``selectedFile`` y limpia los mensajes anteriores.
   *
   * @param {Event} e - Evento de cambio del input de tipo file.
   */
  function handleFileChange(e) {
    selectedFile = e.target.files[0] ?? null
    successMsg = ''
    errorMsg = ''
  }

  /**
   * Inicia la simulación visual de progreso de la barra de carga.
   * La barra avanza en incrementos de 10% cada 120 ms hasta llegar al 90%.
   * El 100% se establece manualmente al recibir la respuesta del backend.
   *
   * @returns {number} ID del intervalo para poder cancelarlo.
   */
  function simulateProgress() {
    progress = 0
    const interval = setInterval(() => {
      if (progress < 90) progress += 10
      else clearInterval(interval)
    }, 120)
    return interval
  }

  /**
   * Maneja el envío del formulario de carga.
   *
   * Flujo de ejecución:
   *   1. Validar que se haya seleccionado un archivo.
   *   2. Validar la extensión del archivo en el cliente.
   *   3. Validar el tamaño del archivo en el cliente.
   *   4. Construir el ``FormData`` con los campos requeridos por el backend.
   *   5. Iniciar la simulación de progreso y enviar la solicitud.
   *   6. En caso de éxito: limpiar el formulario y notificar al padre.
   *   7. En caso de error: mostrar el mensaje de error correspondiente.
   *   8. Restablecer el progreso a 0 con un pequeño retraso visual.
   */
  async function handleUpload() {
    successMsg = ''
    errorMsg = ''

    // Validación: archivo seleccionado
    if (!selectedFile) {
      errorMsg = 'Debes seleccionar un archivo antes de continuar.'
      return
    }

    // Validación de extensión en el cliente (la misma validación se repite en el backend)
    const ext = `.${selectedFile.name.split('.').pop()?.toLowerCase() ?? ''}`
    if (!allowedExtensions.includes(ext)) {
      errorMsg = `Extensión '${ext}' no permitida. Tipos aceptados: ${formattedExtensions}.`
      return
    }

    // Validación de tamaño en el cliente (evita envíos innecesarios al servidor)
    if (selectedFile.size > maxFileSizeMb * 1024 * 1024) {
      errorMsg = `El archivo supera el límite de ${maxFileSizeMb} MB.`
      return
    }

    // Construir el FormData con todos los campos requeridos por el endpoint POST /upload
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
      progress = 100   // completar la barra visualmente al recibir respuesta

      if (!ok) {
        // Error reportado por el backend (validación o almacenamiento)
        errorMsg = data.detail ?? 'Ocurrió un error durante la subida.'
      } else {
        successMsg = data.message ?? 'Archivo subido correctamente.'
        // Limpiar el formulario para permitir una nueva carga de inmediato
        username = ''
        password = ''
        selectedFile = null
        if (fileInputEl) fileInputEl.value = ''
        // Notificar al padre con el nuevo registro para actualizar el historial
        onuploadSuccess?.(data.record)
      }
    } catch {
      // Error de red: el backend no está accesible
      clearInterval(progressInterval)
      errorMsg = 'No se pudo conectar con el backend. Verifica que la API esté en línea.'
    } finally {
      loading = false
      // Resetear la barra de progreso con un pequeño retraso para una transición suave
      setTimeout(() => { progress = 0 }, 1800)
    }
  }
</script>

<div class="upload-form">

  <!-- Campos de credenciales: usuario y contraseña -->
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

  <!-- Selector de archivo con indicación de formatos y tamaño máximo -->
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
    <!-- Texto de ayuda dinámico con los valores obtenidos del backend -->
    <div class="field-hint mt-2">
      Formatos: {formattedExtensions} &nbsp;·&nbsp; Máximo: {maxFileSizeMb} MB
    </div>
  </div>

  <!-- Barra de progreso animada; visible solo mientras progress > 0 -->
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

  <!-- Alerta de éxito; visible solo tras una carga exitosa -->
  {#if successMsg}
    <div class="alert-box alert-box--success mb-4">
      <i class="bi bi-check-circle-fill"></i>
      <span>{successMsg}</span>
    </div>
  {/if}

  <!-- Alerta de error; visible si la validación o la API reportan un fallo -->
  {#if errorMsg}
    <div class="alert-box alert-box--error mb-4">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{errorMsg}</span>
    </div>
  {/if}

  <!-- Botón de envío; desactivado y con spinner mientras la carga está en progreso -->
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
