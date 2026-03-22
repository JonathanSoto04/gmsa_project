<script>
  /**
   * @type {{
   *   selected: string,
   *   onselect: (protocol: string) => void
   * }}
   */
  let { selected = 'nfs', onselect } = $props()

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
      key: 'sftp',
      label: 'SFTP',
      icon: 'bi-shield-lock-fill',
      desc: 'Transferencia segura sobre SSH, ideal para entornos con autenticación protegida.',
      accent: 'proto--sftp',
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

<div class="proto-grid">
  {#each protocols as proto}
    <button
      type="button"
      class={`proto-card ${proto.accent} ${selected === proto.key ? 'is-active' : ''}`}
      onclick={() => onselect(proto.key)}
      aria-pressed={selected === proto.key}
    >
      <div class="proto-card-icon">
        <i class={`bi ${proto.icon}`}></i>
      </div>
      <div class="proto-card-body">
        <div class="proto-card-label">{proto.label}</div>
        <div class="proto-card-desc">{proto.desc}</div>
      </div>
      {#if selected === proto.key}
        <div class="proto-card-check">
          <i class="bi bi-check-lg"></i>
        </div>
      {/if}
    </button>
  {/each}
</div>
