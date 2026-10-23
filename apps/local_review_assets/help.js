/* Contextual help uses the same content as the server-rendered FAQ. */
(() => {
  const dialog = document.getElementById('context-dialog');
  let previousFocus = null;
  if (dialog && typeof dialog.showModal === 'function') {
    const close = () => dialog.close();
    document.getElementById('context-close').addEventListener('click', close);
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) close();
    });
    dialog.addEventListener('close', () => {
      document.getElementById('context-body').replaceChildren();
      if (previousFocus?.isConnected) previousFocus.focus({preventScroll:true});
    });
    document.addEventListener('click', event => {
      const trigger = event.target.closest('[data-help-topic]');
      if (!trigger || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
      const template = document.getElementById(`help-topic-${trigger.dataset.helpTopic}`);
      if (!template) return;
      event.preventDefault();
      previousFocus = trigger;
      document.getElementById('context-title').textContent = template.dataset.title;
      document.getElementById('context-body').replaceChildren(template.content.cloneNode(true));
      document.getElementById('context-more').href = trigger.href;
      dialog.showModal();
      document.getElementById('context-close').focus();
    });
  }

  const openAnchor = () => {
    const target = document.getElementById(location.hash.slice(1));
    if (target?.matches('details')) target.open = true;
  };
  openAnchor();
  window.addEventListener('hashchange', openAnchor);
  document.addEventListener('click', event => {
    if (!event.target.closest('.help-menu')) document.querySelector('.help-menu')?.removeAttribute('open');
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !dialog?.open) {
      const menu = document.querySelector('.help-menu[open]');
      if (menu) {menu.open = false; menu.querySelector('summary').focus();}
    }
  });

  const form = document.getElementById('faq-search-form');
  if (!form) return;
  const input = document.getElementById('faq-search');
  const items = [...document.querySelectorAll('[data-faq-item]')];
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
  const originalState = new Map(items.map(item => [item, item.open]));
  const filter = () => {
    const term = normalize(input.value.trim());
    let count = 0;
    for (const item of items) {
      const matches = !term || normalize(item.textContent).includes(term);
      item.hidden = !matches;
      item.open = term ? matches : originalState.get(item);
      if (matches) count++;
    }
    document.querySelectorAll('[data-faq-category]').forEach(category => {
      category.hidden = ![...category.querySelectorAll('[data-faq-item]')].some(item => !item.hidden);
    });
    document.getElementById('faq-empty').hidden = count > 0;
    document.getElementById('faq-count').textContent = term
      ? `${count} ${count === 1 ? 'pregunta coincide' : 'preguntas coinciden'} con tu búsqueda`
      : `${count} preguntas disponibles`;
  };
  input.addEventListener('input', filter);
  form.addEventListener('submit', event => {event.preventDefault(); filter();});
  document.getElementById('faq-clear').addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    input.value = '';
    const url = new URL(location.href);
    url.searchParams.delete('q');
    history.replaceState(null, '', url);
    filter();
    input.focus();
  });
  filter();
  openAnchor();
})();
