<!--
  Archivo : components/Header.svelte
  Descripción:
    Componente de barra de navegación superior de la aplicación.

    Renderiza el nombre y logo del proyecto junto con los chips de tecnologías
    utilizadas (FastAPI, Svelte 5, Bootstrap 5) y un indicador visual del
    estado de conexión con el backend de la API.

  Props:
    · apiOnline {boolean} — indica si el backend está accesible. Cuando es
      ``true`` se muestra el indicador en verde («API en línea»); cuando es
      ``false`` se muestra en rojo («API desconectada»).

  Estado gestionado:
    Este componente es puramente presentacional; no posee estado reactivo
    propio ni realiza llamadas a la API.
-->

<script>
  /**
   * Props del componente Header.
   * @type {{ apiOnline: boolean }}
   */
  let { apiOnline = false } = $props()
</script>

<header class="app-header">
  <div class="container-fluid px-4">
    <div class="header-inner">

      <!-- Marca del proyecto: icono + nombre completo -->
      <div class="header-brand">
        <div class="brand-icon">
          <i class="bi bi-hdd-rack-fill"></i>
        </div>
        <div class="brand-text">
          <span class="brand-name">GMSA</span>
          <span class="brand-subtitle">Gestor Multiservicio de Almacenamiento</span>
        </div>
      </div>

      <!-- Sección derecha: chips de tecnología e indicador de estado de la API -->
      <div class="header-right">

        <!-- Chips informativos con las tecnologías del stack -->
        <div class="tech-chips">
          <span class="tech-chip">FastAPI</span>
          <span class="tech-chip">Svelte 5</span>
          <span class="tech-chip">Bootstrap 5</span>
        </div>

        <!-- Indicador de estado: cambia de clase CSS según ``apiOnline`` -->
        <div class={`api-status ${apiOnline ? 'api-status--online' : 'api-status--offline'}`}>
          <span class="api-status-dot"></span>
          <span class="api-status-label">{apiOnline ? 'API en línea' : 'API desconectada'}</span>
        </div>

      </div>

    </div>
  </div>
</header>
