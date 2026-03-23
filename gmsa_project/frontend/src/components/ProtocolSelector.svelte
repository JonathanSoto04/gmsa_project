<!--
  Archivo : components/ProtocolSelector.svelte
  Descripción:
    Componente de selección visual del protocolo de almacenamiento destino.

    Renderiza una cuadrícula de tarjetas clicables, una por cada protocolo
    disponible. La tarjeta activa se resalta visualmente con la clase
    ``is-active``. Al hacer clic en una tarjeta se notifica al componente
    padre mediante el callback ``onselect``.

  Props:
    · selected  {string}   — clave del protocolo actualmente seleccionado
                             (p. ej., ``"nfs"``, ``"s3"``).
    · onselect  {Function} — callback invocado con la clave del protocolo
                             elegido cuando el usuario hace clic en una tarjeta.

  Estado gestionado:
    Este componente no posee estado reactivo propio. El estado de selección
    es controlado externamente por el componente padre (``App.svelte``) a
    través del prop ``selected``.

  Datos estáticos:
    La lista ``protocols`` define la configuración visual de cada tarjeta
    (clave, etiqueta, icono, descripción y clase de color de acento).
    En una versión dinámica, esta lista podría obtenerse del endpoint
    ``GET /config`` del backend.
-->

<script>
  /**
   * Props del componente ProtocolSelector.
   * @type {{
   *   selected: string,
   *   onselect: (protocol: string) => void
   * }}
   */
  let { selected = 'nfs', onselect } = $props()

  /**
   * Definición estática de los protocolos disponibles con su metadatos visuales.
   * Cada objeto contiene:
   *   · key    — identificador interno del protocolo (coincide con el backend).
   *   · label  — nombre visible en la tarjeta.
   *   · icon   — clase de Bootstrap Icons para el ícono de la tarjeta.
   *   · desc   — descripción breve del caso de uso del protocolo.
   *   · accent — clase CSS que aplica el color de acento específico del protocolo.
   */
  const protocols = [
    {
      key: 'nfs',
      label: 'NFS',
      icon: 'bi-hdd-network-fill',
      desc: 'Almacenamiento compartido en red, ideal para entornos Linux o rutas montadas.',
      accent: 'proto--nfs',
    },
    {
      key: 'ftp',
      label: 'FTP',
      icon: 'bi-server',
      desc: 'Transferencia tradicional de archivos con autenticación por credenciales.',
      accent: 'proto--ftp',
    },
    {
      key: 's3',
      label: 'S3 / MinIO',
      icon: 'bi-cloud-arrow-up-fill',
      desc: 'Almacenamiento tipo objeto compatible con Amazon S3 para integraciones modernas.',
      accent: 'proto--s3',
    },
    {
      key: 'smb',
      label: 'SMB',
      icon: 'bi-folder-symlink-fill',
      desc: 'Recursos compartidos en entornos Windows o infraestructura empresarial.',
      accent: 'proto--smb',
    },
  ]
</script>

<!-- Cuadrícula de tarjetas de protocolo; una tarjeta por protocolo disponible -->
<div class="proto-grid">
  {#each protocols as proto}
    <!--
      Cada tarjeta es un botón accesible con:
        · aria-pressed — indica si la tarjeta está activa para lectores de pantalla.
        · is-active    — clase CSS aplicada al protocolo seleccionado actualmente.
    -->
    <button
      type="button"
      class={`proto-card ${proto.accent} ${selected === proto.key ? 'is-active' : ''}`}
      onclick={() => onselect(proto.key)}
      aria-pressed={selected === proto.key}
    >
      <!-- Ícono representativo del protocolo -->
      <div class="proto-card-icon">
        <i class={`bi ${proto.icon}`}></i>
      </div>
      <!-- Nombre y descripción del protocolo -->
      <div class="proto-card-body">
        <div class="proto-card-label">{proto.label}</div>
        <div class="proto-card-desc">{proto.desc}</div>
      </div>
      <!-- Marca de verificación visible solo en la tarjeta activa -->
      {#if selected === proto.key}
        <div class="proto-card-check">
          <i class="bi bi-check-lg"></i>
        </div>
      {/if}
    </button>
  {/each}
</div>
