document.addEventListener('DOMContentLoaded', () => {
  const tbody = document.getElementById('filasListado');
  const contador = document.getElementById('contadorListado');
  const botonExcel = document.getElementById('descargarExcel');
  if (!tbody) return;

  const filtros = ['filtroTipoListado', 'filtroSituacion', 'filtroAsignacion', 'filtroEstado']
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  // Si la URL trae ?situacion=Activo (o cualquier filtro), precargar los
  // selects con esos valores antes del primer filtrado.
  const paramsUrl = new URLSearchParams(window.location.search);
  ['tipo', 'situacion', 'asignacion', 'estado'].forEach((clave) => {
    const valor = paramsUrl.get(clave);
    if (!valor) return;
    const idMap = {
      tipo: 'filtroTipoListado', situacion: 'filtroSituacion',
      asignacion: 'filtroAsignacion', estado: 'filtroEstado',
    };
    const el = document.getElementById(idMap[clave]);
    if (el) el.value = valor;
  });

  function construirParams() {
    return new URLSearchParams({
      tipo: document.getElementById('filtroTipoListado')?.value || '',
      situacion: document.getElementById('filtroSituacion')?.value || '',
      asignacion: document.getElementById('filtroAsignacion')?.value || '',
      estado: document.getElementById('filtroEstado')?.value || '',
    });
  }

  function actualizarBotonExcel(params) {
    if (!botonExcel) return;
    const base = botonExcel.dataset.baseUrl || botonExcel.getAttribute('href').split('?')[0];
    botonExcel.dataset.baseUrl = base;
    botonExcel.setAttribute('href', `${base}?${params.toString()}`);
  }

  function actualizarContador() {
    if (!contador) return;
    const total = tbody.querySelectorAll('.fila-vehiculo').length;
    contador.textContent = `${total} vehículo${total === 1 ? '' : 's'}`;
  }

  async function aplicarFiltros() {
    const params = construirParams();
    actualizarBotonExcel(params);

    tbody.classList.add('opacity-50');
    try {
      const resp = await fetch(`${tbody.dataset.filtrarUrl}?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!resp.ok) throw new Error('Error al filtrar el listado');
      tbody.innerHTML = await resp.text();
      actualizarContador();
    } catch (err) {
      console.error(err);
    } finally {
      tbody.classList.remove('opacity-50');
    }
  }

  filtros.forEach((el) => el.addEventListener('change', aplicarFiltros));

  // Carga inicial: el primer render del servidor viene vacío a propósito
  // (para no traer TODA la flota sin filtro alguno de entrada), y además
  // respeta los filtros que vinieran en la URL (ver bloque de arriba).
  aplicarFiltros();
});
