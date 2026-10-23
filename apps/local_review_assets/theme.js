/* Run before the stylesheet so a saved preference applies on the first paint. */
(() => {
  const key = 'pdf-converter:theme';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = value => value === 'light' || value === 'dark';
  let preference = null;
  try {
    const saved = localStorage.getItem(key);
    if (valid(saved)) preference = saved;
  } catch {
    // Browser storage is optional; the control still works for this page.
  }

  function applyTheme() {
    const theme = preference || (system.matches ? 'dark' : 'light');
    root.dataset.theme = theme;
    const button = document.getElementById('theme-toggle');
    if (button) {
      const next = theme === 'dark' ? 'claro' : 'oscuro';
      button.setAttribute('aria-label', `Cambiar a modo ${next}`);
      button.title = `Cambiar a modo ${next}`;
      document.getElementById('theme-label').textContent = `Modo ${next}`;
      button.hidden = false;
    }
  }

  applyTheme();
  root.classList.add('js');
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    applyTheme();
    button.addEventListener('click', () => {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme();
      try {
        localStorage.setItem(key, preference);
      } catch {
        // A rejected write must not undo the theme or interrupt conversion.
      }
    });
  });
  system.addEventListener('change', () => {
    if (!preference) applyTheme();
  });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) {
      preference = valid(event.newValue) ? event.newValue : null;
      applyTheme();
    }
  });
})();
