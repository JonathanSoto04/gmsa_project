<script>
  /** @type {{ apiOnline: boolean }} */
  let { apiOnline = false } = $props()
</script>

<header class="app-header">
  <div class="container-fluid px-4">
    <div class="header-inner">

      <div class="header-brand">
        <div class="brand-icon">
          <i class="bi bi-hdd-rack-fill"></i>
        </div>
        <div class="brand-text">
          <span class="brand-name">GMSA</span>
          <span class="brand-subtitle">Gestor Multiservicio de Almacenamiento</span>
        </div>
      </div>

      <div class="header-right">
        <div class="tech-chips">
          <span class="tech-chip">FastAPI</span>
          <span class="tech-chip">Svelte 5</span>
          <span class="tech-chip">Bootstrap 5</span>
        </div>
        <div class={`api-status ${apiOnline ? 'api-status--online' : 'api-status--offline'}`}>
          <span class="api-status-dot"></span>
          <span class="api-status-label">{apiOnline ? 'API en línea' : 'API desconectada'}</span>
        </div>
      </div>

    </div>
  </div>
</header>
