"""Local, single-user web wrapper around the F0 CLI (apps/convert.py).

Not the F1 web app: no accounts, no database, no queue, no multi-tenancy.
Deployable on a reachable host behind HTTP Basic Auth (see AUTH_USERNAME/
AUTH_PASSWORD below and docs/adr/0006-mvp-railway-hardening.md); each
conversion runs isolated with a hard timeout and memory cap
(apps/conversion_isolation.py) and generated files are swept on a TTL, since
a single trusted user is still exposed to pathological PDFs and unbounded
disk growth. docs/PROTOTIPO_F0.md still defers the real "flujo web con
usuarios, trabajos, storage y cola" to F1. This exists purely so a user can
drag a PDF into a browser instead of typing CLI flags; it calls the exact
same extraction/export functions apps/convert.py does.

Run: python -m apps.local_review_ui
Then open http://127.0.0.1:8420/
"""
from __future__ import annotations

import asyncio
import functools
import html
import os
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_400_BAD_REQUEST

from apps.conversion_isolation import (
    CLEANUP_INTERVAL_SECONDS, RETENTION_HOURS, cleanup_loop, run_isolated,
)
from apps.local_review_help import contextual_templates, help_link, render_help

OUTPUT_ROOT = Path(".generated/web_ui")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # Matches extract_digital's own default limit.
ALLOWED_FORMATS = {"xlsx", "docx", "txt"}
ASSET_ROOT = Path(__file__).with_name("local_review_assets")

# Bump on every user-visible feature/fix so whoever opens the app can tell
# which build they're reviewing without checking git log. Keep the note to
# one short line describing what's new in THIS build, not a full changelog.
APP_VERSION = "0.4.0"
APP_VERSION_DATE = "2026-10-27"
APP_VERSION_NOTE = "Corrige documentos escaneados largos en blanco; recuerda tu configuración; aislamiento y TTL"
FORMAT_INFO = {
    "xlsx": ("Excel", "Tablas y celdas"),
    "docx": ("Word", "Diseño e imágenes"),
    "txt": ("Texto", "Sin formato"),
}

@asynccontextmanager
async def _lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(
        cleanup_loop(OUTPUT_ROOT, RETENTION_HOURS, CLEANUP_INTERVAL_SECONDS))
    try:
        yield
    finally:
        cleanup_task.cancel()


app = FastAPI(title="PDF Converter - F0 local review UI", docs_url=None, redoc_url=None,
              lifespan=_lifespan)
app.mount("/assets", StaticFiles(directory=ASSET_ROOT), name="assets")

# Optional HTTP Basic Auth gate. Unset in local dev (README flow unchanged);
# set both AUTH_USERNAME and AUTH_PASSWORD when running on a reachable host
# (e.g. Railway) since this prototype has no accounts of its own.
AUTH_USERNAME = os.environ.get("AUTH_USERNAME")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD")


def _authorized(request: Request) -> bool:
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        return True
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    import base64

    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
        user, _, pwd = decoded.partition(":")
    except Exception:
        return False
    return secrets.compare_digest(user, AUTH_USERNAME) and secrets.compare_digest(pwd, AUTH_PASSWORD)


# One conversion at a time, matching the product's own stated model ("Un
# usuario y un documento a la vez"). Without this, removing the old
# accidental serialization (extract_digital used to block the single uvicorn
# worker) would let concurrent requests each spawn their own isolated
# subprocess, multiplying memory use. Checking .locked() then entering
# `async with` with no `await` in between is race-free on the single-threaded
# event loop - don't insert an `await` between the two.
CONVERT_CONCURRENCY = int(os.environ.get("CONVERT_CONCURRENCY", "1"))
_convert_semaphore = asyncio.Semaphore(CONVERT_CONCURRENCY)


@app.middleware("http")
async def local_response_headers(request: Request, call_next):
    if not _authorized(request):
        return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=\"PDF Converter\""})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    )
    return response


PAGE_SHELL = ((ASSET_ROOT / "shell.html").read_text(encoding="utf-8")
              .replace("{help_templates}", contextual_templates())
              .replace("{theme_help}", help_link("theme"))
              .replace("{menu_help}", help_link("help"))
              .replace("{app_version_label}", html.escape(f"v{APP_VERSION}"))
              .replace("{app_version_note}", html.escape(f"{APP_VERSION_DATE} · {APP_VERSION_NOTE}"))
              # Cache-busts /assets/* on every version bump: a browser that
              # cached an older app.js/style.css would otherwise keep running
              # stale client code indefinitely after a server-side update.
              .replace("{app_version}", APP_VERSION))


def icon(name: str) -> str:
    paths = {
        "upload": '<path d="M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4"/>',
        "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
        "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
        "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
        "warning": '<path d="m12 3 10 18H2Z"/><path d="M12 9v5m0 3v1"/>',
        "close": '<path d="m6 6 12 12M6 18 18 6"/>',
        "plus": '<path d="M12 5v14M5 12h14"/>',
    }
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{paths[name]}</svg>')


LOCAL_NOTE = f"""
<section class="note-card" aria-labelledby="local-title">
  {icon('shield')}
  <h2 id="local-title">Se queda en tu equipo</h2>
  <p>La conversión se ejecuta en este servidor local, sin enviar tu PDF a un servicio externo.</p>
  <details><summary>Sobre este prototipo</summary>
    <p>Uso local, un documento a la vez. Los archivos se guardan en
    <code>.generated/web_ui/</code> y se eliminan automáticamente pasadas
    {int(RETENTION_HOURS)} horas.</p>
    <p>Los resultados requieren revisión frente al PDF original.</p>
  </details>
</section>"""


def render_form(error: str | None = None, *, selected_formats: set[str] | None = None,
                pages: str = "", ocr: bool = False, docx_warnings: bool = False) -> str:
    selected = {"xlsx", "txt"} if selected_formats is None else selected_formats
    error_html = (f'<div class="error-banner" role="alert" tabindex="-1">'
                  f'<strong>No pudimos convertir el archivo</strong><p>{html.escape(error)}</p>'
                  '<p>Vuelve a seleccionar tu PDF. Conservamos las opciones de conversión.</p></div>'
                  if error else "")
    format_options = "".join(
        f'<label class="format-option"><input type="checkbox" name="formats" value="{ext}" '
        f'aria-describedby="formats-error" {"checked" if ext in selected else ""}>'
        f'<span class="format-tag">{ext.upper()}</span><strong>{info[0]}</strong>'
        f'<span class="hint">{info[1]}</span></label>'
        for ext, info in FORMAT_INFO.items()
    )
    format_summary = " + ".join(ext.upper() for ext in FORMAT_INFO if ext in selected)
    body = f"""
<div class="intro">
  <p class="eyebrow">DE PDF A POSIBILIDADES</p>
  <h1>Tus PDFs, listos para trabajar.</h1>
  <p>Extrae tablas y texto en archivos editables. Elige tu PDF, define la salida y convierte.</p>
</div>
{error_html}
<div class="workspace">
  <form id="convert-form" class="panel" action="/convert" method="post" enctype="multipart/form-data"
        data-restore-options="{'1' if error is None else '0'}">
    <section class="form-section" aria-labelledby="upload-title">
      <div class="section-heading"><span class="step-number" aria-hidden="true">1</span>
        <h2 id="upload-title">Sube tu documento</h2><span class="hint">Un PDF a la vez</span></div>
      <label class="drop-zone" id="drop-zone" for="file">
        <span class="upload-icon">{icon('upload')}</span>
        <span class="drop-title">Arrastra tu PDF aquí</span>
        <span class="hint">o <span class="browse-text">selecciona un archivo</span></span>
        <span class="hint" id="file-hint">Hasta 25 MB · Máximo 100 páginas</span>
      </label>
        <input class="file-input" type="file" id="file" name="file" accept=".pdf,application/pdf"
               aria-label="Seleccionar archivo PDF" aria-describedby="file-hint file-error" required>
      <div class="selected-file" id="selected-file" hidden>
        <span class="file-symbol" aria-hidden="true">PDF</span>
        <div class="file-info" aria-live="polite"><strong class="file-name" id="file-name"></strong>
          <span class="hint" id="file-size"></span></div>
        <div class="action-with-help"><button type="button" class="icon-button" id="remove-file" data-help-action="remove" aria-label="Quitar archivo y elegir otro">{icon('close')}</button>{help_link('remove')}</div>
      </div>
      <p class="field-error" id="file-error" role="alert" hidden></p>
      <div class="upload-actions">
        <div class="field-help">Sobre el archivo {help_link('upload')}</div>
        <div class="submit-area">
          <div class="action-with-help submit-action"><button type="submit" class="primary-button" data-help-action="convert"><span id="submit-label">Convertir PDF</span>{icon('arrow')}</button>{help_link('convert')}</div>
          <p class="submit-note">El PDF original se conserva junto con tus resultados.</p>
          <div id="progress" class="progress" role="status" tabindex="-1" hidden>
            <div class="progress-title"><span class="spinner" aria-hidden="true"></span>Estamos preparando tus archivos</div>
            <p>Espera a que termine la conversión. Los documentos escaneados pueden tardar más.</p>
          </div>
        </div>
      </div>
    </section>
    <section class="form-section" aria-labelledby="formats-title">
      <div class="section-heading"><span class="step-number" aria-hidden="true">2</span>
        <h2 id="formats-title">Elige la salida</h2><span class="hint">Puedes elegir varios</span></div>
      <div class="format-grid" id="formats-group" role="group" aria-labelledby="formats-title" aria-describedby="formats-error">
        {format_options}
      </div>
      <p class="field-error" id="formats-error" role="alert" hidden></p>
      <div class="field-help">Sobre los formatos {help_link('formats')}</div>
      <label class="ocr-option" for="docx-warnings"><input type="checkbox" id="docx-warnings" name="docx_warnings" value="1" {"checked" if docx_warnings else ""}>
        <span><strong>Anexar notas de revisión al Word</strong>
          <span class="hint">Opcional, si eliges Word. Agrega páginas al final; las notas siempre están disponibles en los resultados.</span></span>
      </label>
      <div class="field-help">Sobre el diseño de Word {help_link('docx')}</div>
    </section>
    <section class="form-section" aria-labelledby="options-title">
      <div class="section-heading"><span class="step-number" aria-hidden="true">3</span>
        <h2 id="options-title">Ajusta los detalles</h2></div>
      <div class="options-grid">
        <div><div class="field-label-row"><label class="field-label" for="pages">Páginas <span class="optional">Opcional</span></label>{help_link('pages')}</div>
          <input class="text-input" type="text" id="pages" name="pages" placeholder="Todas las páginas"
                 value="{html.escape(pages, quote=True)}" aria-describedby="pages-hint pages-error" autocomplete="off">
          <p class="hint field-hint" id="pages-hint">Déjalo vacío o escribe, por ejemplo: 1, 3, 5.</p>
          <p class="field-error" id="pages-error" role="alert" hidden></p>
        </div>
        <label class="ocr-option" for="ocr"><input type="checkbox" id="ocr" name="ocr" value="1" {"checked" if ocr else ""}>
          <span><strong>Reconocer texto escaneado</strong>
            <span class="hint">Activa OCR para páginas sin texto seleccionable. Puede tardar más; requiere Tesseract y Poppler instalados.</span></span>
        </label>
        <div class="field-help ocr-help">Sobre OCR {help_link('ocr')}</div>
      </div>
    </section>
  </form>
  <aside class="sidebar" aria-label="Resumen y ayuda">
    <section class="panel summary-card"><h2>Tu conversión</h2>
      <dl class="summary-list">
        <div><dt>Documento</dt><dd id="summary-file">Sin seleccionar</dd></div>
        <div><dt>Salida</dt><dd id="summary-formats">{format_summary or 'Sin seleccionar'}</dd></div>
        <div><dt>Páginas</dt><dd id="summary-pages">{'Selección personalizada' if pages.strip() else 'Todas'}</dd></div>
        <div><dt>OCR</dt><dd id="summary-ocr">{'Activado' if ocr else 'Desactivado'}</dd></div>
      </dl>
    </section>
    {LOCAL_NOTE}
    <div class="sidebar-tip"><h3>Un mejor punto de partida</h3>
      <p>Los PDFs con texto seleccionable ofrecen mejores resultados. Revisa tablas, cifras y saltos de línea antes de usar los archivos.</p></div>
  </aside>
</div>"""
    return PAGE_SHELL.format(body=body, title="Convierte tu PDF")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render_form()


@app.get("/ayuda", response_class=HTMLResponse)
def help_center(q: str = "") -> str:
    return PAGE_SHELL.format(body=render_help(q), title="Ayuda y preguntas frecuentes")


@app.post("/convert", response_class=HTMLResponse)
async def convert(
    file: UploadFile,
    formats: list[str] = Form(default=[]),
    pages: str = Form(default=""),
    ocr: str = Form(default=""),
    docx_warnings: str = Form(default=""),
) -> HTMLResponse:
    selected_formats = {f for f in formats if f in ALLOWED_FORMATS}

    def failure(message: str) -> HTMLResponse:
        return HTMLResponse(
            render_form(message, selected_formats=selected_formats, pages=pages, ocr=bool(ocr),
                        docx_warnings=bool(docx_warnings)),
            status_code=HTTP_400_BAD_REQUEST,
        )

    if not selected_formats:
        return failure("Selecciona al menos un formato de salida.")

    page_numbers = None
    if pages.strip():
        if not re.fullmatch(r"[1-9]\d*(?:\s*,\s*[1-9]\d*)*", pages.strip()):
            return failure("Páginas inválidas: usa números separados por comas, por ejemplo: 1, 3, 5.")
        try:
            page_numbers = [int(p.strip()) for p in pages.split(",")]
        except ValueError:
            return failure("La selección de páginas es demasiado larga. Usa números entre 1 y 100.")
        if len(page_numbers) != len(set(page_numbers)):
            return failure("Hay páginas repetidas. Escribe cada número una sola vez.")

    body = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(body) > MAX_UPLOAD_BYTES:
        return failure("El archivo excede el límite de 25 MB. Elige un PDF más pequeño.")

    job_id = uuid.uuid4().hex
    job_dir = OUTPUT_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    # Server-generated name only; the original filename is never used for I/O.
    source_path = job_dir / "source.pdf"
    source_path.write_bytes(body)

    # No `await` between this check and entering the `async with` below: on
    # the single-threaded event loop that makes the check-then-acquire
    # atomic, so a second concurrent request reliably gets the friendly
    # "busy" response instead of silently queuing behind the first.
    if _convert_semaphore.locked():
        return failure("Ya hay una conversión en curso. Este prototipo procesa un documento "
                        "a la vez: inténtalo de nuevo en unos segundos.")
    async with _convert_semaphore:
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, functools.partial(
            run_isolated, job_dir, source_path, page_numbers=page_numbers, ocr=bool(ocr),
            selected_formats=frozenset(selected_formats), docx_warnings=bool(docx_warnings)))

    if not summary.ok:
        if summary.error_kind == "validation":
            messages = {
                "Invalid PDF signature": "El archivo no es un PDF válido. Selecciona otro documento.",
                "Encrypted PDFs are unsupported": "El PDF está protegido. Usa una copia sin contraseña.",
                "PDF exceeds page limit or has no pages": "El PDF debe tener entre 1 y 100 páginas.",
                "Invalid selected pages": "Alguna página no existe en el PDF. Revisa los números e inténtalo de nuevo.",
                "PDF could not be parsed": "No se pudo leer este PDF. Comprueba que abre correctamente o usa otra copia.",
            }
            return failure(f"Conversión falló: {messages.get(summary.error_message, summary.error_message)}")
        if summary.error_kind == "export_value_error":
            return failure("No se pudo exportar el contenido al formato elegido sin perder información. "
                            "Prueba con TXT o con menos páginas.")
        if summary.error_kind == "timeout":
            return failure("El PDF tardó demasiado en procesarse. Prueba con menos páginas o un "
                            "documento más simple.")
        if summary.error_kind == "memory":
            return failure("El PDF requiere más memoria de la disponible para procesarse. "
                            "Prueba con menos páginas.")
        return failure("Ocurrió un error inesperado al convertir el archivo. Inténtalo de nuevo.")

    warnings = summary.warnings
    friendly_warnings = {
        "UNVALIDATED_EXTRACTION": "Compara los archivos con el PDF original: la calidad de extracción aún no se ha verificado.",
        "OCR_REQUIRED": "Esta página no tiene texto extraíble. Vuelve a convertir con reconocimiento de texto (OCR) activado.",
        "IMAGES_NOT_EXTRACTED": "Las imágenes de esta página no se incluyen en los archivos convertidos.",
        "OCR_FAILED": "No se pudo reconocer el texto. Comprueba que Tesseract y Poppler están instalados.",
        "DOCX_LAYOUT_APPROXIMATE": "Word conserva texto editable, tamaños, colores y posiciones aproximadas. Revisa la distribución y los saltos de página.",
        "DOCX_FONT_SUBSTITUTED": "Algunas fuentes del PDF se sustituyeron por equivalentes de Word. El ajuste del texto puede variar.",
        "DOCX_TABLE_AS_POSITIONED_TEXT": "Un panel complejo se conservó como texto editable en su posición; sus campos no forman una tabla de Word.",
        "LAYOUT_ASSETS_UNAVAILABLE": "No se pudieron conservar todas las imágenes o los gráficos de esta página. Compara con el PDF original.",
        "OCR_LAYOUT_APPROXIMATE": "El texto reconocido con OCR conserva un orden aproximado; su distribución original requiere ajuste.",
        "ROTATED_TEXT_LAYOUT": "Hay texto girado. Revisa su orientación en Word.",
        "TABLE_DECORATION_FILTERED": "Se separaron los bordes de tabla de sus fondos de color. Revisa la estructura y las celdas frente al PDF.",
        "EMPTY_PAGE": "Esta página no contiene texto ni elementos gráficos detectados.",
    }
    warning_items = "".join(
        f'<li><span class="warning-page">Página {w["page_number"]}</span>'
        f'<p>{html.escape(friendly_warnings.get(w["code"], w["message"]))}</p>'
        f'<details><summary>Detalle técnico</summary><div class="technical-detail">'
        f'<code>{html.escape(w["code"])}</code> · {html.escape(w["message"])}</div></details></li>'
        for w in warnings
    )
    downloads = "".join(
        f'<div class="action-with-help download-row"><a class="download-card" href="/download/{job_id}/result.{ext}" aria-label="Descargar {info[0]}" data-help-action="{ext}" download>'
        f'<span class="file-symbol" aria-hidden="true">{ext.upper()}</span>'
        f'<span class="file-info"><strong>Descargar {info[0]}</strong>'
        f'<span class="hint">.{ext} · {(job_dir / f"result.{ext}").stat().st_size / 1024:.1f} KB</span></span>'
        f'{icon("download")}</a>{help_link(ext)}</div>'
        for ext, info in FORMAT_INFO.items() if ext in selected_formats
    )
    preview = (f'<pre class="text-preview" tabindex="0" aria-label="Texto extraído">{html.escape(summary.text_preview)}</pre>'
               if summary.text_preview.strip() else '<p class="hint">No se extrajo texto. Si el PDF es un escaneo, vuelve a convertir con OCR activado.</p>')
    preview_note = ('<p class="hint field-hint">Vista limitada a 6 000 caracteres. Consulta el texto completo en los archivos de salida.</p>'
                     if summary.text_truncated else '')
    body_html = f"""
<div class="result-heading">
  <div class="intro"><p class="eyebrow">CONVERSIÓN COMPLETADA</p>
    <h1>Tu PDF, un paso más allá.</h1><p>{html.escape(file.filename or 'Documento PDF')}</p></div>
  <div class="action-with-help"><a class="secondary-button" href="/" data-help-action="new">{icon('plus')}Convertir otro PDF</a>{help_link('new')}</div>
</div>
<div class="review-banner">{icon('warning')}<div><strong>Archivos generados. Revisión pendiente.</strong>
  <p>Comprueba el contenido frente al PDF original antes de utilizarlo. Estado: <code>needs_review</code>.</p></div>{help_link('review')}</div>
<div class="metrics" aria-label="Resumen del resultado">
  <div class="panel metric"><strong>{summary.pages_processed} <span>/ {summary.page_count}</span></strong><span>Páginas procesadas</span></div>
  <div class="panel metric"><strong>{summary.table_count}</strong><span>Tablas detectadas</span></div>
  <div class="panel metric"><strong>{len(selected_formats)}</strong><span>Archivos de salida</span></div>
</div>
<div class="workspace">
  <div class="result-stack">
    <section class="panel result-section"><h2>Descarga tus archivos</h2><p class="hint">Elige un formato para guardarlo en tu equipo.</p>
      <div class="download-list">{downloads}</div></section>
    <section class="panel result-section"><h2>Vista del texto extraído</h2><p class="hint">Una primera mirada al contenido, sin formato.</p>
      {preview}{preview_note}</section>
    <section class="panel result-section"><h2>Notas para tu revisión ({len(warnings)})</h2>
      <ul class="warnings-list">{warning_items}</ul></section>
  </div>
  <aside class="sidebar" aria-label="Ayuda para revisar">
    <section class="panel summary-card"><h2>Antes de continuar</h2>
      <p class="hint">Revisa cifras, encabezados y celdas combinadas. Word aproxima el diseño e incluye las imágenes y gráficos que se pudieron conservar. Las fuentes y la edición pueden modificar los saltos de página.</p>
      <details><summary>Datos de la extracción</summary><p class="hint">JSON con contenido, procedencia y advertencias para una revisión técnica.</p>
        <div class="action-with-help"><a class="technical-download" href="/download/{job_id}/document.ir.json" data-help-action="json" download>Descargar document.ir.json</a>{help_link('json')}</div></details>
    </section>
    {LOCAL_NOTE}
  </aside>
</div>
"""
    return HTMLResponse(PAGE_SHELL.format(body=body_html, title="Tus resultados"))


@app.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str) -> FileResponse:
    job_dir = (OUTPUT_ROOT / job_id).resolve()
    if not job_dir.is_relative_to(OUTPUT_ROOT.resolve()):
        raise HTTPException(status_code=404, detail="Not found")
    target = (job_dir / filename).resolve()
    if not target.is_file() or not target.is_relative_to(job_dir) or filename not in {
        "result.xlsx", "result.docx", "result.txt", "document.ir.json",
    }:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target, filename=filename)


def main() -> None:
    import uvicorn

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8420"))
    print(f"PDF Converter (F0 local review UI) - abre http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
