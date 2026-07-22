/**
 * Modal genérico para mostrar "popup details" cargados por AJAX.
 * data-modal-url="/vehiculos/fragmento/ABC-123/" abre el popup con ese
 * contenido al hacer clic. También expuesto como window.VehiculosModal
 * para invocarlo desde otro sistema (ej. el botón del mapa).
 */
(function () {
  const TAILWIND_CDN = 'https://cdn.tailwindcss.com';
  let overlayEl = null;
  let cajaEl = null;
  let promesaTailwind = null;

  function asegurarTailwind() {
    if (window.tailwind) return Promise.resolve();
    if (promesaTailwind) return promesaTailwind;
    promesaTailwind = new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = TAILWIND_CDN;
      script.onload = resolve;
      script.onerror = resolve;
      document.head.appendChild(script);
    });
    return promesaTailwind;
  }

  function construirOverlay() {
    if (overlayEl) return;
    overlayEl = document.createElement('div');
    overlayEl.id = 'vehiculos-modal-overlay';
    overlayEl.style.cssText =
      'position:fixed;inset:0;background:rgba(15,23,42,0.55);' +
      'display:none;align-items:flex-start;justify-content:center;' +
      'padding:2.5rem 1rem;overflow-y:auto;z-index:9999;';

    cajaEl = document.createElement('div');
    cajaEl.style.cssText =
      'background:#F1F3F2;border-radius:1rem;max-width:80rem;width:100%;' +
      'position:relative;box-shadow:0 20px 60px rgba(0,0,0,0.35);';

    const botonCerrar = document.createElement('button');
    botonCerrar.type = 'button';
    botonCerrar.setAttribute('aria-label', 'Cerrar');
    botonCerrar.textContent = '✕';
    botonCerrar.style.cssText =
      'position:absolute;top:0.75rem;right:0.75rem;width:2.25rem;height:2.25rem;' +
      'border-radius:9999px;background:#fff;border:1px solid #e2e8f0;' +
      'font-size:1rem;line-height:1;cursor:pointer;z-index:1;';
    botonCerrar.addEventListener('click', cerrar);

    const contenido = document.createElement('div');
    contenido.id = 'vehiculos-modal-contenido';
    contenido.style.cssText = 'padding:1.5rem;';
    contenido.innerHTML = '<p style="text-align:center;color:#94a3b8;padding:2rem;">Cargando…</p>';

    cajaEl.appendChild(botonCerrar);
    cajaEl.appendChild(contenido);
    overlayEl.appendChild(cajaEl);
    document.body.appendChild(overlayEl);

    overlayEl.addEventListener('click', (e) => {
      if (e.target === overlayEl) cerrar();
    });
  }

  async function abrir(url) {
    construirOverlay();
    overlayEl.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    const contenido = document.getElementById('vehiculos-modal-contenido');
    contenido.innerHTML = '<p style="text-align:center;color:#94a3b8;padding:2rem;">Cargando…</p>';

    await asegurarTailwind();

    try {
      const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      contenido.innerHTML = await resp.text();
    } catch (err) {
      contenido.innerHTML =
        '<p style="text-align:center;color:#e11d48;padding:2rem;">No se pudo cargar el detalle. Intenta de nuevo.</p>';
      console.error('VehiculosModal:', err);
    }
  }

  function cerrar() {
    if (overlayEl) overlayEl.style.display = 'none';
    document.body.style.overflow = '';

    // Callback opcional de una sola vez: solo lo usan los flujos que
    // necesitan "regresar" a algo al cerrar (ej. la tarjeta de Vehículos
    // dentro del modal nativo del mapa) — el resto de los usos de este
    // modal (ícono del mapa, Parque Vehicular, /vehiculos/) no lo tocan,
    // así que ahí simplemente no hace nada distinto a lo de siempre.
    if (typeof window._vehiculosAlCerrarCallback === 'function') {
      const cb = window._vehiculosAlCerrarCallback;
      window._vehiculosAlCerrarCallback = null;
      cb();
    }
  }

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-modal-url]');
    if (!el) return;
    e.preventDefault();
    abrir(el.dataset.modalUrl);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') cerrar();
  });

  window.VehiculosModal = { abrir, cerrar };

  window.filtrarListadoModal = async function () {
    const tbody = document.getElementById('modalListadoTabla');
    if (!tbody) return;

    const params = new URLSearchParams({
      tipo: document.getElementById('modalFiltroTipo')?.value || '',
      situacion: document.getElementById('modalFiltroSituacion')?.value || '',
      asignacion: document.getElementById('modalFiltroAsignacion')?.value || '',
      estado: document.getElementById('modalFiltroEstado')?.value || '',
    });

    tbody.style.opacity = '0.5';
    try {
      const resp = await fetch(`/vehiculos/api/listado/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!resp.ok) throw new Error('Error al filtrar el listado');
      tbody.innerHTML = await resp.text();
    } catch (err) {
      console.error('filtrarListadoModal:', err);
    } finally {
      tbody.style.opacity = '1';
    }
  };

  window.limpiarFiltrosListadoModal = function () {
    ['modalFiltroTipo', 'modalFiltroSituacion', 'modalFiltroAsignacion', 'modalFiltroEstado'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    window.filtrarListadoModal();
  };

  // --- Hover para la tarjeta "Parque Vehicular" del mapa orgánico ---
  // Esa tarjeta (en mapa_activo.html) solo tenía onclick; esto le agrega
  // "mantener el cursor encima abre solo", igual que en /vehiculos/,
  // sin tener que volver a editar mapa_activo.html a mano.
  document.addEventListener('DOMContentLoaded', () => {
    const tarjeta = document.getElementById('card_vehiculos');
    if (!tarjeta || typeof window.mostrarParqueVehicular !== 'function') return;

    let temporizador = null;
    tarjeta.addEventListener('mouseenter', () => {
      temporizador = setTimeout(() => window.mostrarParqueVehicular(), 400);
    });
    tarjeta.addEventListener('mouseleave', () => {
      clearTimeout(temporizador);
    });
  });

  // --- Íconos de vehículos por inmueble en el mapa ---
  // Un marcador con el ícono de auto por inmueble con vehículos
  // (coordenadas reales), con una insignia mostrando el conteo; clic
  // abre la lista de vehículos en ese inmueble.
  function intentarAgregarCapaVehiculos() {
    const listo = typeof map !== 'undefined' && map && typeof map.addSource === 'function' && typeof maplibregl !== 'undefined';
    if (!listo) {
      setTimeout(intentarAgregarCapaVehiculos, 500);
      return;
    }
    if (window._vehiculosMarcadoresAgregados) {
      console.log('[vehiculos-mapa] ya se habían agregado antes, se omite');
      return;
    }
    window._vehiculosMarcadoresAgregados = true;

    console.log('[vehiculos-mapa] mapa detectado, esperando 1.5s a que termine de asentarse...');
    setTimeout(agregarMarcadoresVehiculos, 1500);
  }

  function agregarMarcadoresVehiculos() {
    console.log('[vehiculos-mapa] agregando marcadores ahora');

    fetch('/vehiculos/api/mapa-ubicaciones/')
      .then((resp) => resp.json())
      .then((geojson) => {
        console.log('[vehiculos-mapa] geojson recibido, features =', geojson.features ? geojson.features.length : 'N/A');
        if (!geojson.features || !geojson.features.length) return;

        // Contenedor propio superpuesto al mapa — no usamos
        // maplibregl.Marker (su reposicionamiento automático no está
        // funcionando bien en esta página); en su lugar calculamos la
        // posición en pantalla nosotros mismos con map.project(), que es
        // el mismo método que usa el mapa internamente, y la actualizamos
        // cada vez que el mapa se mueve/hace zoom.
        const contenedorMapa = map.getContainer ? map.getContainer() : document.getElementById('map');
        if (!contenedorMapa) {
          console.error('[vehiculos-mapa] no se encontró el contenedor del mapa');
          return;
        }
        if (getComputedStyle(contenedorMapa).position === 'static') {
          contenedorMapa.style.position = 'relative';
        }

        const capa = document.createElement('div');
        capa.id = 'vehiculos-capa-iconos';
        capa.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;';
        contenedorMapa.appendChild(capa);

        const marcadores = geojson.features.map((feature) => {
          const [lng, lat] = feature.geometry.coordinates;
          const props = feature.properties;

          const el = document.createElement('div');
          el.title = `${props.nombre} (${props.total} vehículo${props.total === 1 ? '' : 's'})`;
          el.style.cssText =
            'position:absolute;width:32px;height:32px;background:#9A0A38;border-radius:50%;' +
            'border:2px solid #ffffff;box-shadow:0 1px 4px rgba(0,0,0,0.4);cursor:pointer;' +
            'display:flex;align-items:center;justify-content:center;pointer-events:auto;' +
            'transform:translate(-50%,-50%);';
          el.innerHTML =
            '<img src="/static/vehiculos/icons/vehiculo.svg" style="width:16px;height:16px;filter:invert(1) brightness(2);" alt="">' +
            '<span style="position:absolute;top:-5px;right:-5px;background:#ffffff;color:#9A0A38;' +
            'font-size:10px;font-weight:700;border-radius:9999px;min-width:16px;height:16px;' +
            'display:flex;align-items:center;justify-content:center;padding:0 3px;' +
            'border:1px solid #9A0A38;">' + props.total + '</span>';

          el.addEventListener('click', () => {
            if (props.placa_unica) {
              window.VehiculosModal.abrir(`/vehiculos/fragmento/${encodeURIComponent(props.placa_unica)}/`);
            } else {
              window.VehiculosModal.abrir(`/vehiculos/api/popover/?inmueble=${encodeURIComponent(props.nombre)}`);
            }
          });

          capa.appendChild(el);
          return { el, lngLat: [lng, lat] };
        });

        function reposicionarTodos() {
          marcadores.forEach(({ el, lngLat }) => {
            const punto = map.project(lngLat);
            // Desplazamiento fijo (arriba a la derecha) para que no se
            // encime exactamente con el ícono nativo de la oficina, que
            // está en el mismo punto geográfico.
            el.style.left = (punto.x + 16) + 'px';
            el.style.top = (punto.y - 16) + 'px';
          });
        }

        reposicionarTodos();
        map.on('move', reposicionarTodos);
        map.on('zoom', reposicionarTodos);
        map.on('resize', reposicionarTodos);
        window.addEventListener('resize', reposicionarTodos);

        console.log('[vehiculos-mapa] marcadores agregados con exito (posicionamiento manual)');
      })
      .catch((err) => console.error('[vehiculos-mapa] No se pudo cargar la capa de vehículos en el mapa:', err));
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Solo intenta en la página que sí tiene el mapa (evita ruido en /vehiculos/).
    if (document.getElementById('card_vehiculos')) {
      console.log('[vehiculos-mapa] card_vehiculos encontrado, iniciando espera del mapa...');
      intentarAgregarCapaVehiculos();
    } else {
      console.log('[vehiculos-mapa] card_vehiculos NO encontrado en esta página');
    }
  });
})();
