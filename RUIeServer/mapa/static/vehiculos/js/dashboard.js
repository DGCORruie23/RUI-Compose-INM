document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('gridTipos');
  if (!grid) return;

  const filtros = ['filtroTipo', 'filtroSituacionTipos', 'filtroEstadoTipos']
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  async function aplicarFiltros() {
    const params = new URLSearchParams({
      solo_con_unidades: document.getElementById('filtroTipo')?.value || '',
      situacion: document.getElementById('filtroSituacionTipos')?.value || '',
      estado: document.getElementById('filtroEstadoTipos')?.value || '',
    });

    grid.classList.add('opacity-50');
    try {
      const resp = await fetch(`${grid.dataset.filtrarUrl}?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!resp.ok) throw new Error('Error al filtrar');
      grid.innerHTML = await resp.text();
    } catch (err) {
      console.error(err);
    } finally {
      grid.classList.remove('opacity-50');
    }
  }

  filtros.forEach((el) => el.addEventListener('change', aplicarFiltros));
});
