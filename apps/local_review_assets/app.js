/* Progressive enhancement: upload and conversion also work without JavaScript. */
document.documentElement.classList.add('js');
const form = document.querySelector('#convert-form');
document.querySelector('.error-banner')?.focus({ preventScroll: true });
if (form) {
  const fileInput = form.querySelector('#file');
  const dropZone = form.querySelector('#drop-zone');
  const selectedFile = form.querySelector('#selected-file');
  const pages = form.querySelector('#pages');
  const formats = [...form.querySelectorAll('[name="formats"]')];
  const ocr = form.querySelector('#ocr');
  const docxWarnings = form.querySelector('#docx-warnings');
  const submit = form.querySelector('[type="submit"]');
  let busy = false;

  // Remember the last submitted options (formats, pages, OCR, Word annex) so
  // "Convertir otro PDF" starts from where the user left off instead of the
  // hardcoded defaults. Only restore on a fresh form load (data-restore-options
  // is "0" when the server just re-rendered the user's own input after a
  // validation error, which must win over anything saved here).
  const OPTIONS_KEY = 'pdf-converter:last-options';
  if (form.dataset.restoreOptions === '1') {
    try {
      const saved = JSON.parse(localStorage.getItem(OPTIONS_KEY) || 'null');
      if (saved) {
        if (Array.isArray(saved.formats) && saved.formats.length) {
          formats.forEach(input => { input.checked = saved.formats.includes(input.value); });
        }
        if (typeof saved.pages === 'string') pages.value = saved.pages;
        if (typeof saved.ocr === 'boolean') ocr.checked = saved.ocr;
        if (docxWarnings && typeof saved.docxWarnings === 'boolean') docxWarnings.checked = saved.docxWarnings;
      }
    } catch {
      // Browser storage is optional; the form still works with its defaults.
    }
    updateFormats();
    validatePages();
  }

  function saveOptions() {
    try {
      localStorage.setItem(OPTIONS_KEY, JSON.stringify({
        formats: formats.filter(input => input.checked).map(input => input.value),
        pages: pages.value,
        ocr: ocr.checked,
        docxWarnings: docxWarnings ? docxWarnings.checked : false,
      }));
    } catch {
      // A rejected write must not block the conversion itself.
    }
  }

  function fieldError(input, id, message) {
    const element = document.getElementById(id);
    element.textContent = message;
    element.hidden = !message;
    input.setAttribute('aria-invalid', String(Boolean(message)));
  }

  function updateFile() {
    const file = fileInput.files[0];
    let error = '';
    if (file && !/\.pdf$/i.test(file.name) && file.type !== 'application/pdf') {
      error = 'Elige un archivo PDF. Otros tipos de archivo no se pueden convertir.';
    } else if (file && file.size > 25 * 1024 * 1024) {
      error = 'El PDF supera los 25 MB. Elige un archivo más pequeño.';
    } else if (file && file.size === 0) {
      error = 'El archivo está vacío. Elige otro PDF.';
    }
    fileInput.setCustomValidity(error);
    fieldError(fileInput, 'file-error', error);
    selectedFile.hidden = !file;
    dropZone.hidden = Boolean(file);
    if (file) {
      document.getElementById('file-name').textContent = file.name;
      document.getElementById('file-size').textContent = `${new Intl.NumberFormat('es-MX', { maximumFractionDigits: 2 }).format(file.size / 1024 / 1024)} MB · PDF`;
      document.getElementById('remove-file').focus({ preventScroll: true });
    }
    document.getElementById('summary-file').textContent = file ? '1 PDF seleccionado' : 'Sin seleccionar';
  }

  function validatePages() {
    const value = pages.value.trim();
    const numbers = value.split(',').map(x => x.trim());
    let error = '';
    if (value && (!/^[1-9]\d*(\s*,\s*[1-9]\d*)*$/.test(value) || new Set(numbers).size !== numbers.length)) {
      error = 'Usa páginas sin repetir, separadas por comas, por ejemplo: 1, 3, 5.';
    }
    pages.setCustomValidity(error);
    fieldError(pages, 'pages-error', error);
    document.getElementById('summary-pages').textContent = value ? 'Selección personalizada' : 'Todas';
    return !error;
  }

  function updateFormats() {
    const selected = formats.filter(input => input.checked);
    const error = selected.length ? '' : 'Selecciona al menos un formato para continuar.';
    formats[0].setCustomValidity(error);
    fieldError(document.getElementById('formats-group'), 'formats-error', error);
    document.getElementById('summary-formats').textContent = selected.map(input => input.value.toUpperCase()).join(' + ') || 'Sin seleccionar';
  }

  fileInput.addEventListener('change', updateFile);
  document.getElementById('remove-file').addEventListener('click', () => {
    if (busy) return;
    fileInput.value = '';
    updateFile();
    fileInput.focus();
  });
  let dragDepth = 0;
  dropZone.addEventListener('dragenter', event => {
    event.preventDefault();
    if (!busy) { dragDepth += 1; dropZone.classList.add('dragging'); }
  });
  dropZone.addEventListener('dragover', event => event.preventDefault());
  dropZone.addEventListener('dragleave', () => {
    dragDepth = Math.max(0, dragDepth - 1);
    if (!dragDepth) dropZone.classList.remove('dragging');
  });
  dropZone.addEventListener('drop', event => {
    event.preventDefault();
    dragDepth = 0;
    dropZone.classList.remove('dragging');
    if (busy) return;
    const files = event.dataTransfer.files;
    if (files.length !== 1) {
      fieldError(fileInput, 'file-error', 'Arrastra un solo PDF a la vez.');
      return;
    }
    fileInput.files = files;
    updateFile();
  });
  pages.addEventListener('input', () => {
    pages.setCustomValidity('');
    fieldError(pages, 'pages-error', '');
  });
  pages.addEventListener('blur', validatePages);
  formats.forEach(input => input.addEventListener('change', updateFormats));
  ocr.addEventListener('change', () => {
    document.getElementById('summary-ocr').textContent = ocr.checked ? 'Activado' : 'Desactivado';
  });
  form.addEventListener('invalid', event => {
    if (event.target === fileInput && !fileInput.files.length) {
      fieldError(fileInput, 'file-error', 'Selecciona un PDF para continuar.');
    }
  }, true);
  form.addEventListener('submit', event => {
    if (busy) { event.preventDefault(); return; }
    if (!validatePages() || !form.reportValidity()) { event.preventDefault(); return; }
    saveOptions();
    busy = true;
    form.setAttribute('aria-busy', 'true');
    submit.disabled = true;
    document.getElementById('submit-label').textContent = 'Convirtiendo tu PDF…';
    document.getElementById('progress').hidden = false;
    document.getElementById('progress').focus({ preventScroll: true });
  });
  window.addEventListener('pageshow', () => {
    busy = false;
    form.removeAttribute('aria-busy');
    submit.disabled = false;
    document.getElementById('submit-label').textContent = 'Convertir PDF';
    document.getElementById('progress').hidden = true;
    updateFile();
    updateFormats();
    validatePages();
    document.getElementById('summary-ocr').textContent = ocr.checked ? 'Activado' : 'Desactivado';
  });
}
