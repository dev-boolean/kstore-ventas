// KStore · atajos de teclado estilo terminal
// 0-9 abren la opción del menú, ↑↓ se mueven por el menú, Enter la abre, Esc vuelve al inicio.
(function () {
  const menu = Array.from(document.querySelectorAll('.menu a'));

  // Al cargar, el foco queda en la opción activa para poder usar las flechas de una vez
  const activo = document.querySelector('.menu a.activo');
  if (activo && !document.querySelector('[autofocus]')) activo.focus({ preventScroll: true });

  document.addEventListener('keydown', function (e) {
    const t = e.target;
    const tag = (t.tagName || '').toLowerCase();

    // Ctrl+Enter ejecuta la consola SQL
    if (t.id === 'sql' && e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      t.form.submit();
      return;
    }
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    if (/^[0-9]$/.test(e.key)) {
      const a = menu.find(function (x) { return x.dataset.tecla === e.key; });
      if (a) { e.preventDefault(); location.href = a.href; }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      location.href = menu[0].href;
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      let i = menu.indexOf(document.activeElement);
      if (i === -1 && document.activeElement !== document.body) return;
      if (i === -1) i = menu.findIndex(function (x) { return x.classList.contains('activo'); });
      e.preventDefault();
      i = (i + (e.key === 'ArrowDown' ? 1 : -1) + menu.length) % menu.length;
      menu[i].focus();
    }
  });

  // Consola SQL: elegir un ejemplo lo copia en el área de texto
  const ejemplo = document.getElementById('ejemplo');
  if (ejemplo) {
    ejemplo.addEventListener('change', function () {
      if (ejemplo.value) document.getElementById('sql').value = ejemplo.value;
    });
  }

  // Confirmación antes de acciones que borran datos
  document.querySelectorAll('form[data-confirmar]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      if (!confirm(f.dataset.confirmar)) ev.preventDefault();
    });
  });
})();
