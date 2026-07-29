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
  // Pila de navegacion dentro del modal (para el boton "Regresar" de la
  // ficha): cada vez que abrir() carga una URL nueva, guarda la anterior
  // aqui antes de reemplazarla, para poder volver sin recargar todo.
  let historialModal = [];
  let urlActual = null;
  // Cache de /vehiculos/api/mapa-ubicaciones/, llenado por
  // agregarMarcadoresVehiculos() mas abajo. Permite que la tarjeta de
  // "Vehiculos" del modal nativo del mapa (mapa_activo.html) sepa, sin
  // pedir nada nuevo al backend, si el inmueble tiene un solo vehiculo
  // (y por lo tanto puede ir directo a su ficha) o varios.
  const ubicacionesVehiculosPorInmueble = {};

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
    if (urlActual && urlActual !== url) {
      historialModal.push(urlActual);
    }
    urlActual = url;

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

  // Vuelve al contenido anterior dentro del mismo modal (botón "Regresar"
  // de la ficha). Si no hay historial (se abrió directo, sin pasar por
  // otra vista antes), simplemente cierra el modal.
  function regresar() {
    const anterior = historialModal.pop();
    if (anterior) {
      urlActual = null; // evita que abrir() vuelva a apilar la ficha que se deja
      abrir(anterior);
    } else {
      cerrar();
    }
  }

  function cerrar() {
    if (overlayEl) overlayEl.style.display = 'none';
    document.body.style.overflow = '';
    historialModal = [];
    urlActual = null;

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

  // Misma ficha detallada que usa el icono del auto en el mapa: si el
  // inmueble tiene un solo vehiculo, va directo a su ficha; si no hay
  // datos en cache todavia o tiene mas de uno, cae al resumen agregado
  // (mismo comportamiento de siempre, sin romper nada).
  function abrirParaInmueble(nombreInmueble) {
    const info = ubicacionesVehiculosPorInmueble[nombreInmueble];
    if (info && info.total === 1 && info.placa_unica) {
      abrir(`/vehiculos/fragmento/${encodeURIComponent(info.placa_unica)}/`);
    } else {
      abrir(`/vehiculos/fragmento/resumen-estado/?inmueble=${encodeURIComponent(nombreInmueble)}`);
    }
  }

  window.VehiculosModal = { abrir, cerrar, abrirParaInmueble, regresar };

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

      // Cuenta las filas reales (la fila de "sin resultados" no trae la
      // clase "fila-vehiculo", asi que no se cuenta como 1 resultado falso).
      const contador = document.getElementById('modalContadorListado');
      if (contador) {
        const total = tbody.querySelectorAll('tr.fila-vehiculo').length;
        contador.textContent = `${total} resultado${total === 1 ? '' : 's'}`;
      }
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

  // Botones del menu lateral de la ficha ("Informacion de la Unidad",
  // "Asignacion y Logistica", "Combustible", "Kilometraje"): saltan a su
  // seccion correspondiente con scroll suave. scrollIntoView() funciona
  // igual sin importar si el contenedor que hace scroll es la ventana
  // completa (pagina /vehiculos/<placa>/) o el overlay del modal del mapa.
  window.vehIrASeccion = function (idSeccion) {
    const el = document.getElementById(idSeccion);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Filtro de fecha (kilometraje/combustible) de la ficha de detalle.
  // Vive aqui y no en un <script> dentro de _detalle_contenido.html
  // porque ese fragmento tambien se carga via innerHTML dentro del modal
  // del mapa (VehiculosModal.abrir), y los navegadores NO ejecutan
  // <script> insertados por innerHTML -- solo funcionaria en la pagina
  // completa /vehiculos/<placa>/, no dentro del modal.
  window.vehFiltrarHistorial = function (placa, limpiar) {
    const inicio = document.getElementById('vehFiltroFechaInicio');
    const fin = document.getElementById('vehFiltroFechaFin');
    const params = new URLSearchParams();
    if (!limpiar) {
      if (inicio && inicio.value) params.set('fecha_inicio', inicio.value);
      if (fin && fin.value) params.set('fecha_fin', fin.value);
    }
    fetch(`/vehiculos/fragmento/${encodeURIComponent(placa)}/?${params.toString()}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then((resp) => resp.text())
      .then((html) => {
        const temporal = document.createElement('div');
        temporal.innerHTML = html;
        const nuevaFicha = temporal.querySelector('#vehDetalleFicha');
        const actual = document.getElementById('vehDetalleFicha');
        if (actual && nuevaFicha) actual.replaceWith(nuevaFicha);
      })
      .catch((err) => console.error('vehFiltrarHistorial:', err));
  };

  // --- Galería de fotos con zoom (estilo e-commerce) para la ficha ---
  // Vive aquí por la misma razón que vehFiltrarHistorial: el fragmento
  // que la usa (_detalle_contenido.html) se carga via innerHTML dentro
  // del modal del mapa, y ahí los <script> insertados así no corren.
  let vehGaleriaOverlay = null;
  let vehGaleriaFotos = [];
  let vehGaleriaIndice = 0;
  let vehGaleriaZoom = 1;
  let vehGaleriaPanX = 0;
  let vehGaleriaPanY = 0;
  let vehGaleriaKmActual = '';

  function vehActualizarTransformGaleria() {
    const img = document.getElementById('vehGaleriaImgActual');
    if (img) img.style.transform = `translate(${vehGaleriaPanX}px, ${vehGaleriaPanY}px) scale(${vehGaleriaZoom})`;
  }

  function vehMostrarFotoGaleria() {
    const item = vehGaleriaFotos[vehGaleriaIndice];
    if (!item) return;
    const img = document.getElementById('vehGaleriaImgActual');
    const etiqueta = document.getElementById('vehGaleriaEtiqueta');
    vehGaleriaZoom = 1;
    vehGaleriaPanX = 0;
    vehGaleriaPanY = 0;
    if (img) img.src = item.src;
    vehActualizarTransformGaleria();
    if (etiqueta) {
      let texto = `${item.label} · ${vehGaleriaIndice + 1}/${vehGaleriaFotos.length}`;
      if (vehGaleriaKmActual) texto += ` · Odómetro: ${vehGaleriaKmActual} km`;
      etiqueta.textContent = texto;
    }
  }

  function vehCambiarFotoGaleria(delta) {
    if (vehGaleriaFotos.length < 2) return;
    vehGaleriaIndice = (vehGaleriaIndice + delta + vehGaleriaFotos.length) % vehGaleriaFotos.length;
    vehMostrarFotoGaleria();
  }

  function vehCerrarGaleria() {
    if (vehGaleriaOverlay) vehGaleriaOverlay.style.display = 'none';
    document.body.style.overflow = '';
  }

  function vehConstruirGaleriaOverlay() {
    if (vehGaleriaOverlay) return;

    vehGaleriaOverlay = document.createElement('div');
    vehGaleriaOverlay.style.cssText =
      'position:fixed;inset:0;background:rgba(0,0,0,0.88);display:none;' +
      'align-items:center;justify-content:center;z-index:10000;user-select:none;';

    const marco = document.createElement('div');
    marco.style.cssText = 'position:relative;max-width:88vw;max-height:80vh;overflow:hidden;cursor:grab;';

    const img = document.createElement('img');
    img.id = 'vehGaleriaImgActual';
    img.style.cssText =
      'max-width:88vw;max-height:80vh;display:block;transform-origin:center;' +
      'transition:transform 0.12s ease-out;pointer-events:none;';
    marco.appendChild(img);

    const etiqueta = document.createElement('p');
    etiqueta.id = 'vehGaleriaEtiqueta';
    etiqueta.style.cssText = 'position:fixed;top:1rem;left:0;right:0;text-align:center;color:#fff;font-size:0.85rem;font-weight:600;';

    const ayuda = document.createElement('p');
    ayuda.textContent = 'Rueda del mouse o doble clic para zoom · Arrastra para mover · Esc para salir';
    ayuda.style.cssText = 'position:fixed;bottom:1rem;left:0;right:0;text-align:center;color:rgba(255,255,255,0.65);font-size:0.75rem;';

    const botonCerrar = document.createElement('button');
    botonCerrar.type = 'button';
    botonCerrar.textContent = '✕';
    botonCerrar.setAttribute('aria-label', 'Cerrar');
    botonCerrar.style.cssText =
      'position:fixed;top:0.75rem;right:1rem;width:2.5rem;height:2.5rem;border-radius:9999px;' +
      'background:#fff;border:none;font-size:1.1rem;cursor:pointer;z-index:1;';
    botonCerrar.addEventListener('click', vehCerrarGaleria);

    const botonAnterior = document.createElement('button');
    botonAnterior.type = 'button';
    botonAnterior.innerHTML = '←';
    botonAnterior.setAttribute('aria-label', 'Foto anterior');
    botonAnterior.style.cssText =
      'position:fixed;left:1rem;top:50%;transform:translateY(-50%);width:2.75rem;height:2.75rem;' +
      'border-radius:9999px;background:#fff;border:none;font-size:1.25rem;cursor:pointer;z-index:1;';
    botonAnterior.addEventListener('click', () => vehCambiarFotoGaleria(-1));

    const botonSiguiente = document.createElement('button');
    botonSiguiente.type = 'button';
    botonSiguiente.innerHTML = '→';
    botonSiguiente.setAttribute('aria-label', 'Foto siguiente');
    botonSiguiente.style.cssText =
      'position:fixed;right:1rem;top:50%;transform:translateY(-50%);width:2.75rem;height:2.75rem;' +
      'border-radius:9999px;background:#fff;border:none;font-size:1.25rem;cursor:pointer;z-index:1;';
    botonSiguiente.addEventListener('click', () => vehCambiarFotoGaleria(1));

    vehGaleriaOverlay.appendChild(marco);
    vehGaleriaOverlay.appendChild(etiqueta);
    vehGaleriaOverlay.appendChild(ayuda);
    vehGaleriaOverlay.appendChild(botonCerrar);
    vehGaleriaOverlay.appendChild(botonAnterior);
    vehGaleriaOverlay.appendChild(botonSiguiente);
    document.body.appendChild(vehGaleriaOverlay);

    vehGaleriaOverlay.addEventListener('click', (e) => {
      if (e.target === vehGaleriaOverlay) vehCerrarGaleria();
    });

    // Zoom con la rueda del mouse (sin límite de "foco" en el punto exacto,
    // pero suficiente para acercar/alejar como en un e-commerce).
    marco.addEventListener('wheel', (e) => {
      e.preventDefault();
      vehGaleriaZoom = Math.min(4, Math.max(1, vehGaleriaZoom + (e.deltaY < 0 ? 0.35 : -0.35)));
      if (vehGaleriaZoom === 1) {
        vehGaleriaPanX = 0;
        vehGaleriaPanY = 0;
      }
      vehActualizarTransformGaleria();
    });

    // Doble clic para alternar zoom rápido.
    img.addEventListener('dblclick', () => {
      vehGaleriaZoom = vehGaleriaZoom > 1 ? 1 : 2.5;
      vehGaleriaPanX = 0;
      vehGaleriaPanY = 0;
      vehActualizarTransformGaleria();
    });

    // Arrastrar para mover la imagen cuando está con zoom aplicado.
    let arrastrando = false;
    let inicioX = 0;
    let inicioY = 0;
    marco.addEventListener('mousedown', (e) => {
      if (vehGaleriaZoom <= 1) return;
      arrastrando = true;
      inicioX = e.clientX - vehGaleriaPanX;
      inicioY = e.clientY - vehGaleriaPanY;
      marco.style.cursor = 'grabbing';
    });
    window.addEventListener('mousemove', (e) => {
      if (!arrastrando) return;
      vehGaleriaPanX = e.clientX - inicioX;
      vehGaleriaPanY = e.clientY - inicioY;
      vehActualizarTransformGaleria();
    });
    window.addEventListener('mouseup', () => {
      arrastrando = false;
      marco.style.cursor = 'grab';
    });
  }

  window.vehAbrirGaleria = function (elClicado) {
    // Arma la lista del carrusel leyendo el DOM (no una lista fija), asi
    // solo entran las fotos que ese vehiculo realmente tiene.
    const contenedor = elClicado.closest('[data-veh-galeria]');
    const nodos = contenedor ? contenedor.querySelectorAll('[data-veh-foto]') : [elClicado];
    vehGaleriaFotos = Array.from(nodos).map((n) => ({ src: n.src, label: n.dataset.label || '' }));
    vehGaleriaIndice = Math.max(0, vehGaleriaFotos.findIndex((f) => f.src === elClicado.src));
    vehGaleriaKmActual = (contenedor && contenedor.dataset.kmActual) || '';

    vehConstruirGaleriaOverlay();
    vehGaleriaOverlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    vehMostrarFotoGaleria();
  };

  document.addEventListener('keydown', (e) => {
    if (!vehGaleriaOverlay || vehGaleriaOverlay.style.display !== 'flex') return;
    if (e.key === 'Escape') vehCerrarGaleria();
    if (e.key === 'ArrowLeft') vehCambiarFotoGaleria(-1);
    if (e.key === 'ArrowRight') vehCambiarFotoGaleria(1);
  });

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
        (geojson.features || []).forEach((feature) => {
          ubicacionesVehiculosPorInmueble[feature.properties.nombre] = feature.properties;
        });
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
          // Icono azul celeste y mas chico que el de la oficina (18px vs
          // los 32px originales), para que se note que es un dato
          // secundario/extra sobre el mismo punto, no el icono principal.
          el.style.cssText =
            'position:absolute;width:18px;height:18px;background:#0EA5E9;border-radius:50%;' +
            'border:2px solid #ffffff;box-shadow:0 1px 4px rgba(0,0,0,0.4);cursor:pointer;' +
            'display:flex;align-items:center;justify-content:center;pointer-events:auto;' +
            'transform:translate(-50%,-50%);';
          const iconoAuto = (window.VEH_ICONOS && window.VEH_ICONOS.auto) || '/static/vehiculos/icons/vehiculo.svg';
          el.innerHTML =
            '<img src="' + iconoAuto + '" style="width:9px;height:9px;filter:invert(1) brightness(2);" alt="">' +
            '<span style="position:absolute;top:-4px;right:-4px;background:#ffffff;color:#0EA5E9;' +
            'font-size:7px;font-weight:700;border-radius:9999px;min-width:11px;height:11px;' +
            'display:flex;align-items:center;justify-content:center;padding:0 2px;' +
            'border:1px solid #0EA5E9;">' + props.total + '</span>';

          el.addEventListener('click', () => {
            // Misma decision (ficha directa si hay 1 solo vehiculo, si no
            // el resumen agregado) que ya usa la tarjeta de "Vehiculos" del
            // icono de oficina -- se reutiliza abrirParaInmueble() en vez
            // de duplicar la logica aqui, para que ambos iconos siempre
            // muestren lo mismo aunque cambie la cantidad de vehiculos.
            window.VehiculosModal.abrirParaInmueble(props.nombre);
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
    const tarjetaVehiculos = document.getElementById('card_vehiculos');
    if (!tarjetaVehiculos) {
      console.log('[vehiculos-mapa] card_vehiculos NO encontrado en esta página');
      return;
    }
    // Los iconos de auto ya NO se agregan solos al cargar la pagina --
    // solo se activan la primera vez que el usuario da clic en la tarjeta
    // "Parque Vehicular" (intentarAgregarCapaVehiculos ya se protege con
    // window._vehiculosMarcadoresAgregados para no duplicarlos despues).
    tarjetaVehiculos.addEventListener('click', () => {
      console.log('[vehiculos-mapa] tarjeta Parque Vehicular clicada, activando iconos del mapa...');
      intentarAgregarCapaVehiculos();
    });
  });

  // --- Conteo real en la tarjeta "Parque Vehicular" del menu ---
  // El numero ahi era un "32" fijo, dejado de una carga de prueba vieja y
  // que nunca se actualizaba con los datos reales. Se reemplaza por una
  // consulta al total real al cargar la pagina.
  document.addEventListener('DOMContentLoaded', () => {
    const contador = document.getElementById('menu_vehiculos');
    if (!contador) return;
    fetch('/vehiculos/api/conteo/')
      .then((resp) => resp.json())
      .then((data) => { contador.innerText = data.total; })
      .catch((err) => console.error('[vehiculos-mapa] no se pudo obtener el conteo real:', err));
  });
})();
