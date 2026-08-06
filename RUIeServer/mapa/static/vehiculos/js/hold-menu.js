/**
 * Menú desplegable universal sobre categorías del dashboard (Activos,
 * Sedán, etc.): funciona con mouse (solo pasar el cursor y dejarlo quieto),
 * touchpad (con o sin "tap to click"), clic derecho / gesto de 2 dedos,
 * y pantallas táctiles reales.
 *
 * - Mouse: pasar el cursor y dejarlo ~0.35s abre la lista sola, sin clic.
 * - Un clic simple también abre de inmediato (respaldo para touchpads/touch
 *   donde el hover no aplica de forma confiable).
 * - Mantener presionado (mouse, touch) y clic derecho también funcionan.
 * Todo apunta a la misma función abrirPopover(), así que nunca se duplica
 * ni se abre dos veces para el mismo elemento.
 *
 * Uso en un template:
 *   <li data-hold-url="{% url 'vehiculos:popover_vehiculos' %}"
 *       data-hold-params="situacion=Activo">Activos</li>
 */
(function () {
  const HOLD_MS = 450;
  const MOVE_TOLERANCIA = 8; // px — solo aplica a touch (ver nota abajo)

  let holdTimer = null;
  let holdPendiente = false; // bandera explícita: no confiar en si holdTimer es "truthy"
  let activeEl = null;
  let popoverEl = null;
  let inicioX = 0;
  let inicioY = 0;

  const HOVER_MS = 350;
  const HOVER_CIERRE_MS = 250;
  let hoverAbrirTimer = null;
  let hoverCerrarTimer = null;
  let hoveredTrigger = null;

  function estaSobre(el, otro) {
    return !!(el && otro && (el === otro || (el.contains && el.contains(otro))));
  }

  function cerrarPopover() {
    clearTimeout(hoverAbrirTimer);
    clearTimeout(hoverCerrarTimer);
    hoveredTrigger = null;
    if (popoverEl) {
      popoverEl.remove();
      popoverEl = null;
    }
    if (activeEl) {
      activeEl.classList.remove('hold-activo');
      activeEl = null;
    }
  }

  function posicionarPopover(el) {
    const rect = el.getBoundingClientRect();
    const anchoPopover = 260;
    let left = window.scrollX + rect.left;
    if (left + anchoPopover > window.scrollX + window.innerWidth - 16) {
      left = window.scrollX + window.innerWidth - anchoPopover - 16;
    }
    popoverEl.style.position = 'absolute';
    popoverEl.style.top = `${window.scrollY + rect.bottom + 6}px`;
    popoverEl.style.left = `${left}px`;
    popoverEl.style.width = `${anchoPopover}px`;
  }

  async function abrirPopover(el) {
    if (activeEl === el && popoverEl) return; // ya está abierto para este mismo elemento
    cerrarPopover();
    activeEl = el;
    el.classList.add('hold-activo');

    popoverEl = document.createElement('div');
    popoverEl.className =
      'z-[10000] bg-white rounded-xl border border-slate-200 shadow-xl p-1.5 max-h-72 overflow-y-auto';
    popoverEl.innerHTML = '<p class="px-3 py-4 text-xs text-slate-400 text-center">Cargando…</p>';
    document.body.appendChild(popoverEl);
    posicionarPopover(el);

    const url = `${el.dataset.holdUrl}?${el.dataset.holdParams || ''}`;
    try {
      const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!resp.ok) throw new Error('Error al cargar el popover');
      popoverEl.innerHTML = await resp.text();
      posicionarPopover(el);
    } catch (err) {
      popoverEl.innerHTML = '<p class="px-3 py-4 text-xs text-rose-500 text-center">Ocurrió un error al cargar.</p>';
    }
  }

  function iniciarHold(x, y, target) {
    const el = target.closest('[data-hold-params]');
    if (!el) return;
    inicioX = x;
    inicioY = y;
    clearTimeout(holdTimer);
    holdPendiente = true;
    holdTimer = setTimeout(() => {
      holdPendiente = false;
      abrirPopover(el);
    }, HOLD_MS);
  }

  function cancelarHold() {
    clearTimeout(holdTimer);
    holdPendiente = false;
  }

  // --- Mouse: solo mousedown/mouseup/mouseleave cancelan, NO el movimiento
  // (un mouse físico tiembla unos px durante ~1s de clic sostenido; cancelar
  // por eso impedía que el popover se abriera casi siempre).
  document.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    iniciarHold(e.clientX, e.clientY, e.target);
  });
  document.addEventListener('mouseup', cancelarHold);
  document.addEventListener('mouseleave', cancelarHold, true);

  // --- Touch: sí cancela por movimiento grande (para distinguir de un scroll) ---
  document.addEventListener('touchstart', (e) => {
    const t = e.touches[0];
    iniciarHold(t.clientX, t.clientY, e.target);
  }, { passive: true });
  document.addEventListener('touchmove', (e) => {
    if (!holdPendiente) return;
    const t = e.touches[0];
    if (Math.abs(t.clientX - inicioX) > MOVE_TOLERANCIA || Math.abs(t.clientY - inicioY) > MOVE_TOLERANCIA) {
      cancelarHold();
    }
  });
  document.addEventListener('touchend', cancelarHold);

  // --- Hover automático: pasar el cursor y dejarlo quieto abre solo ---
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-hold-params]');
    if (el) {
      if (el === hoveredTrigger) return;
      hoveredTrigger = el;
      clearTimeout(hoverCerrarTimer);
      clearTimeout(hoverAbrirTimer);
      hoverAbrirTimer = setTimeout(() => abrirPopover(el), HOVER_MS);
      return;
    }
    if (popoverEl && (e.target === popoverEl || popoverEl.contains(e.target))) {
      clearTimeout(hoverCerrarTimer);
    }
  });

  document.addEventListener('mouseout', (e) => {
    const el = e.target.closest('[data-hold-params]');
    if (el) {
      if (estaSobre(el, e.relatedTarget)) return;
      clearTimeout(hoverAbrirTimer);
      hoveredTrigger = null;
      if (estaSobre(popoverEl, e.relatedTarget)) return;
      hoverCerrarTimer = setTimeout(() => {
        if (activeEl === el) cerrarPopover();
      }, HOVER_CIERRE_MS);
      return;
    }
    if (popoverEl && (e.target === popoverEl || popoverEl.contains(e.target))) {
      if (estaSobre(activeEl, e.relatedTarget)) return;
      hoverCerrarTimer = setTimeout(() => cerrarPopover(), HOVER_CIERRE_MS);
    }
  });

  // --- Clic derecho: disparador alterno e inmediato (touchpads sin hold real) ---
  document.addEventListener('contextmenu', (e) => {
    const el = e.target.closest('[data-hold-params]');
    if (!el) return;
    e.preventDefault();
    cancelarHold();
    abrirPopover(el);
  });

  // --- Clic simple: SIEMPRE abre de inmediato si no estaba ya abierto ---
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-hold-params]');
    if (el) {
      if (activeEl === el && popoverEl) return;
      cancelarHold();
      abrirPopover(el);
      return;
    }
    if (popoverEl && !popoverEl.contains(e.target) && (!activeEl || !activeEl.contains(e.target))) {
      cerrarPopover();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') cerrarPopover();
  });
  window.addEventListener('scroll', () => {
    if (activeEl) posicionarPopover(activeEl);
  }, true);
})();
