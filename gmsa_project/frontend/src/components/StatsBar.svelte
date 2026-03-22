<script>
  /** @type {{ history: Array }} */
  let { history = [] } = $props()

  let total    = $derived(history.length)
  let success  = $derived(history.filter(i => i.status === 'Éxito').length)
  let errors   = $derived(history.filter(i => i.status === 'Error').length)
  let lastProto = $derived(history.length > 0 ? history[0].protocol : '—')

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
      valueClass: errors > 0 ? 'text-danger' : '',
    },
    {
      label: 'Último protocolo',
      value: lastProto,
      icon: 'bi-hdd-network-fill',
      colorClass: 'stat-icon--purple',
      small: true,
    },
  ])
</script>

<div class="row g-3 mb-4 mb-lg-5">
  {#each cards as card}
    <div class="col-sm-6 col-xl-3">
      <div class="stat-card glass-panel">
        <div class={`stat-icon ${card.colorClass}`}>
          <i class={`bi ${card.icon}`}></i>
        </div>
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
