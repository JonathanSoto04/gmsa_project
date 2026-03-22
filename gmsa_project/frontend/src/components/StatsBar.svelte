<!--
  Archivo : components/StatsBar.svelte
  Descripción:
    Componente que renderiza una fila de tarjetas con estadísticas resumidas
    del historial de cargas de archivos.

    Las métricas se calculan de forma reactiva a partir del array ``history``
    recibido como prop, por lo que se actualizan automáticamente cada vez
    que se añade o elimina un registro del historial.

  Props:
    · history {Array} — lista de registros de historial. Cada elemento debe
      contener al menos los campos ``status`` (``"Éxito"`` | ``"Error"``)
      y ``protocol`` (cadena de texto en mayúsculas).

  Estado derivado (reactivo):
    · total     — número total de cargas registradas.
    · success   — cantidad de cargas con estado «Éxito».
    · errors    — cantidad de cargas con estado «Error».
    · lastProto — protocolo utilizado en la carga más reciente (primero del array).
    · cards     — array de objetos de configuración para renderizar cada tarjeta.

  Estado gestionado:
    Este componente es puramente presentacional y de solo lectura. No modifica
    el historial ni realiza llamadas a la API.
-->

<script>
  /**
   * Props del componente StatsBar.
   * @type {{ history: Array }}
   */
  let { history = [] } = $props()

  // Valores derivados del historial; se recalculan automáticamente cuando
  // el prop ``history`` cambia gracias al sistema reactivo de Svelte 5.
  let total    = $derived(history.length)
  let success  = $derived(history.filter(i => i.status === 'Éxito').length)
  let errors   = $derived(history.filter(i => i.status === 'Error').length)

  /** Protocolo de la carga más reciente. El guion «—» se muestra si el historial está vacío. */
  let lastProto = $derived(history.length > 0 ? history[0].protocol : '—')

  /**
   * Configuración de las tarjetas estadísticas.
   * Se define como valor derivado para que se actualice cuando cambien
   * los valores calculados de los que depende.
   */
  const cards = $derived([
    {
      label: 'Total de cargas',
      value: total,
      icon: 'bi-cloud-upload-fill',
      colorClass: 'stat-icon--blue',
    },
    {
      label: 'Exitosas',
      value: success,
      icon: 'bi-check-circle-fill',
      colorClass: 'stat-icon--green',
      valueClass: 'text-success',
    },
    {
      label: 'Con errores',
      value: errors,
      icon: 'bi-x-circle-fill',
      colorClass: 'stat-icon--red',
      // Solo aplica la clase de color de error si hay al menos un error.
      valueClass: errors > 0 ? 'text-danger' : '',
    },
    {
      label: 'Último protocolo',
      value: lastProto,
      icon: 'bi-hdd-network-fill',
      colorClass: 'stat-icon--purple',
      small: true,   // fuente más pequeña para valores de texto largo
    },
  ])
</script>

<!-- Fila de tarjetas estadísticas; una tarjeta por columna en pantallas grandes -->
<div class="row g-3 mb-4 mb-lg-5">
  {#each cards as card}
    <div class="col-sm-6 col-xl-3">
      <div class="stat-card glass-panel">
        <!-- Icono de la tarjeta con color temático -->
        <div class={`stat-icon ${card.colorClass}`}>
          <i class={`bi ${card.icon}`}></i>
        </div>
        <!-- Etiqueta y valor numérico o textual de la estadística -->
        <div class="stat-body">
          <div class="stat-label">{card.label}</div>
          <div class={`stat-value ${card.valueClass ?? ''} ${card.small ? 'stat-value--sm' : ''}`}>
            {card.value}
          </div>
        </div>
      </div>
    </div>
  {/each}
</div>
