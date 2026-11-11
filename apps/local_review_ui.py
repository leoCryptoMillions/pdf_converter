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
import logging
import os
import re
import secrets
import threading
import time
from contextlib import asynccontextmanager
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_400_BAD_REQUEST

from apps.conversion_isolation import (
    CLEANUP_INTERVAL_SECONDS, RETENTION_HOURS, ConversionSummary, cleanup_loop, prune_old_jobs, run_isolated,
)
from apps.job_store import create_job, publish_job, read_metadata, remove_job
from apps.local_review_help import contextual_templates, help_link, render_help
from apps.request_guard import BoundedMultipartParser, MultiPartException, RequestGuard, RequestTooLarge, UploadFile
from apps.runtime_config import settings

logger = logging.getLogger("pdf_converter.web")

OUTPUT_ROOT = Path(".generated/web_ui")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # Matches extract_digital's own default limit.
ALLOWED_FORMATS = {"xlsx", "docx", "txt"}
ASSET_ROOT = Path(__file__).with_name("local_review_assets")

# Bump on every user-visible feature/fix so whoever opens the app can tell
# which build they're reviewing without checking git log. Keep the note to
# one short line describing what's new in THIS build, not a full changelog.
APP_VERSION = "0.7.0"
APP_VERSION_DATE = "2026-11-10"
APP_VERSION_NOTE = "Límites de carga, memoria y acceso verificados; notas de revisión completas"
FORMAT_INFO = {
    "xlsx": ("Excel", "Tablas y celdas"),
    "docx": ("Word", "Diseño e imágenes"),
    "txt": ("Texto", "Sin formato"),
}

@asynccontextmanager
async def _lifespan(app: FastAPI):
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(prune_old_jobs, OUTPUT_ROOT, RETENTION_HOURS)
    cleanup_task = asyncio.create_task(
        cleanup_loop(OUTPUT_ROOT, RETENTION_HOURS, CLEANUP_INTERVAL_SECONDS))
    try:
        yield
    finally:
        tasks = list(_active_conversions.items())
        for task, cancel in tasks:
            cancel.set()
        if tasks:
            await asyncio.gather(*(task for task, _ in tasks), return_exceptions=True)
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(title="PDF Converter - F0 local review UI", docs_url=None, redoc_url=None,
              lifespan=_lifespan)
app.mount("/assets", StaticFiles(directory=ASSET_ROOT), name="assets")

# Optional HTTP Basic Auth gate. Unset in local dev (README flow unchanged);
# set both AUTH_USERNAME and AUTH_PASSWORD when running on a reachable host
# (e.g. Railway) since this prototype has no accounts of its own.
AUTH_USERNAME = settings.username
AUTH_PASSWORD = settings.password


def _authorized(request: Request) -> bool:
    if not AUTH_USERNAME and not AUTH_PASSWORD:
        return settings.mode == "local"
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        return False
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    import base64

    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
        user, separator, pwd = decoded.partition(":")
        if not separator:
            return False
    except Exception:
        return False
    user_ok = secrets.compare_digest(user.encode("utf-8"), AUTH_USERNAME.encode("utf-8"))
    password_ok = secrets.compare_digest(pwd.encode("utf-8"), AUTH_PASSWORD.encode("utf-8"))
    return user_ok and password_ok


# One conversion at a time, matching the product's own stated model ("Un
# usuario y un documento a la vez"). Without this, removing the old
# accidental serialization (extract_digital used to block the single uvicorn
# worker) would let concurrent requests each spawn their own isolated
# subprocess, multiplying memory use. Checking .locked() then entering
# `async with` with no `await` in between is race-free on the single-threaded
# event loop - don't insert an `await` between the two.
CONVERT_CONCURRENCY = 1
_convert_semaphore = asyncio.Semaphore(1)
_active_conversions: dict[asyncio.Task, threading.Event] = {}


app.add_middleware(RequestGuard, root=lambda: OUTPUT_ROOT, semaphore=lambda: _convert_semaphore,
                   authorized=_authorized, render_error=lambda message: render_form(message),
                   max_upload=lambda: MAX_UPLOAD_BYTES)


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
  <h2 id="local-title">{'Se queda en tu equipo' if settings.mode == 'local' else 'Tus archivos se guardan en este servidor'}</h2>
  <p>{'La conversión se ejecuta en tu equipo.' if settings.mode == 'local' else 'Tu PDF se carga y convierte en el servidor al que te conectaste.'}
  No se envía a servicios externos de conversión.</p>
  <details><summary>Sobre este prototipo</summary>
    <p>Un documento a la vez. Las descargas caducan {RETENTION_HOURS:g} horas
    después de la carga; el servidor elimina los archivos en el siguiente barrido.
    Las copias que descargues se conservan hasta que las elimines.</p>
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
    return PAGE_SHELL.format(body=body, title="PDF Converter")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render_form()


@app.get("/ayuda", response_class=HTMLResponse)
def help_center(q: str = "") -> str:
    return PAGE_SHELL.format(body=render_help(q), title="Ayuda y preguntas frecuentes · PDF Converter")


@app.get("/health")
def health():
    return {"status": "ready", "version": APP_VERSION, "mode": settings.mode,
            "conversion_active": _convert_semaphore.locked(),
            "memory_backend": "windows_job_object" if os.name == "nt" else "rlimit_as"}


@app.post("/convert", response_class=HTMLResponse)
async def convert(request: Request) -> HTMLResponse:
    if not request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
        return HTMLResponse(render_form("Sube el PDF con el formulario de conversión."), status_code=400)
    parser = BoundedMultipartParser(request.headers, request.stream(), MAX_UPLOAD_BYTES)
    try:
        form = await parser.parse()
    except RequestTooLarge:
        return HTMLResponse(render_form("El archivo excede el límite de 25 MB."), status_code=413)
    except (MultiPartException, ValueError):
        return HTMLResponse(render_form("El formulario no es válido: carga un PDF y revisa las opciones."), status_code=400)
    try:
        files = form.getlist("file")
        allowed = {"file", "formats", "pages", "ocr", "docx_warnings"}
        if (len(files) != 1 or not isinstance(files[0], UploadFile) or
                any(key not in allowed for key in form) or
                any(not isinstance(value, str) for key, value in form.multi_items() if key != "file") or
                any(len(form.getlist(key)) > 1 for key in ("pages", "ocr", "docx_warnings"))):
            return HTMLResponse(render_form("Carga un único PDF y revisa las opciones."), status_code=400)
        return await _convert_document(files[0], formats=form.getlist("formats"),
            pages=form.get("pages", ""), ocr=form.get("ocr", ""),
            docx_warnings=form.get("docx_warnings", ""), admission=request.state.conversion_admission)
    finally:
        await form.close()


def _execute_job(job_dir, job_lease, source_path, cancel, **options):
    summary = ConversionSummary(ok=False, error_kind="crash")
    try:
        summary = run_isolated(job_dir, source_path, cancel_event=cancel, **options)
        if cancel.is_set():
            summary = ConversionSummary(ok=False, error_kind="cancelled")
        if summary.ok:
            publish_job(job_dir)
    except OSError as exc:
        logger.warning("job_storage_failed job_id=%s error_type=%s", job_dir.name, type(exc).__name__)
        summary = ConversionSummary(ok=False, error_kind="storage")
    except Exception as exc:
        logger.error("job_failed job_id=%s error_type=%s", job_dir.name, type(exc).__name__)
        summary = ConversionSummary(ok=False, error_kind="crash")
    finally:
        job_lease.close()
        if not summary.ok:
            remove_job(OUTPUT_ROOT, job_dir)
    return summary


async def _supervise_job(job_dir, job_lease, source_path, cancel, **options):
    future = asyncio.get_running_loop().run_in_executor(None, functools.partial(
        _execute_job, job_dir, job_lease, source_path, cancel, **options))
    try:
        return await asyncio.shield(future)
    except asyncio.CancelledError:
        cancel.set()
        # Executor threads cannot be cancelled. Keep ownership until the child exits.
        await asyncio.shield(future)
        raise


async def _convert_document(
    file: UploadFile,
    *, formats: list[str], pages: str, ocr: str, docx_warnings: str, admission,
) -> HTMLResponse:
    selected_formats = {f for f in formats if f in ALLOWED_FORMATS}

    def failure(message: str, status_code: int = HTTP_400_BAD_REQUEST) -> HTMLResponse:
        return HTMLResponse(
            render_form(message, selected_formats=selected_formats, pages=pages, ocr=bool(ocr),
                        docx_warnings=bool(docx_warnings)),
            status_code=status_code,
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
        return failure("El archivo excede el límite de 25 MB. Elige un PDF más pequeño.", 413)

    job_dir = None
    job_lease = None
    try:
        job_dir, job_lease = create_job(OUTPUT_ROOT, RETENTION_HOURS)
        source_path = job_dir / "source.pdf"
        source_path.write_bytes(body)
    except OSError:
        if job_lease:
            job_lease.close()
        if job_dir:
            remove_job(OUTPUT_ROOT, job_dir)
        return failure("No se pudo guardar el PDF. Comprueba el espacio disponible.", 503)

    cancel = threading.Event()
    task = asyncio.create_task(_supervise_job(job_dir, job_lease, source_path, cancel,
        page_numbers=page_numbers, ocr=bool(ocr), selected_formats=frozenset(selected_formats),
        docx_warnings=bool(docx_warnings)))
    admission.task = task
    _active_conversions[task] = cancel
    task.add_done_callback(lambda completed: _active_conversions.pop(completed, None))
    try:
        summary = await asyncio.shield(task)
    except asyncio.CancelledError:
        cancel.set()
        raise
    job_id = job_dir.name
    artifact_dir = job_dir / "artifacts"

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
        if summary.error_kind == "isolation":
            return failure("No se pudo activar el límite de memoria. Revisa la instalación antes de convertir.", 503)
        if summary.error_kind == "storage":
            return failure("No hay espacio suficiente para guardar los resultados. Inténtalo más tarde.", 503)
        return failure("Ocurrió un error inesperado al convertir el archivo. Inténtalo de nuevo.")

    warnings = summary.warnings
    friendly_warnings = {
        "SOURCE_GLYPH_UNMAPPED": "Hay caracteres del PDF que no se pudieron decodificar. Se conservan como marcadores (cid:...). Compáralos con el original antes de usar el texto.",
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
        f'<li><span class="warning-page">Página {w["page_number"]}'
        f'{html.escape(" · " + w["table_id"]) if w.get("table_id") else ""}'
        f'{" · fila " + str(w["row_index"] + 1) if w.get("row_index") is not None else ""}'
        f'{" · columna " + str(w["col_index"] + 1) if w.get("col_index") is not None else ""}</span>'
        f'<p>{html.escape(friendly_warnings.get(w["code"], w["message"]))}</p>'
        f'<details><summary>Detalle técnico</summary><div class="technical-detail">'
        f'<code>{html.escape(w["code"])}</code> · {html.escape(w["message"])}</div></details></li>'
        for w in warnings
    )
    downloads = "".join(
        f'<div class="action-with-help download-row"><a class="download-card" href="/download/{job_id}/result.{ext}" aria-label="Descargar {info[0]}" data-help-action="{ext}" download>'
        f'<span class="file-symbol" aria-hidden="true">{ext.upper()}</span>'
        f'<span class="file-info"><strong>Descargar {info[0]}</strong>'
        f'<span class="hint">.{ext} · {(artifact_dir / f"result.{ext}").stat().st_size / 1024:.1f} KB</span></span>'
        f'{icon("download")}</a>{help_link(ext)}</div>'
        for ext, info in FORMAT_INFO.items() if ext in selected_formats
    )
    preview = (f'<pre class="text-preview" tabindex="0" aria-label="Texto extraído">{html.escape(summary.text_preview)}</pre>'
               if summary.text_preview.strip() else '<p class="hint">No se extrajo texto. Si el PDF es un escaneo, vuelve a convertir con OCR activado.</p>')
    preview_note = ('<p class="hint field-hint">Vista limitada a 6 000 caracteres. Consulta el texto completo en los archivos de salida.</p>'
                     if summary.text_truncated else '')
    expires = datetime.fromtimestamp(read_metadata(job_dir)["expires_at"], timezone.utc)
    expiry_label = expires.strftime("%Y-%m-%d %H:%M UTC")
    warning_total = summary.warning_count or len(warnings)
    warning_limit_note = (f'<p>Mostramos las primeras {len(warnings)} notas; el informe descargable contiene las {warning_total}.</p>'
                          if warning_total > len(warnings) else '')
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
      <p class="hint">Descargas disponibles hasta <time datetime="{expires.isoformat()}">{expiry_label}</time>.</p>
      <div class="download-list">{downloads}</div></section>
    <section class="panel result-section"><h2>Vista del texto extraído</h2><p class="hint">Una primera mirada al contenido, sin formato.</p>
      {preview}{preview_note}</section>
    <section class="panel result-section"><h2>Notas para tu revisión ({warning_total})</h2>
      {warning_limit_note}<p><a href="/download/{job_id}/warnings.json" download>Descargar todas las notas de revisión</a></p>
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
    return HTMLResponse(PAGE_SHELL.format(body=body_html, title="PDF Converter"))


@app.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str) -> FileResponse:
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise HTTPException(status_code=404, detail="Not found")
    job_dir = (OUTPUT_ROOT / job_id).resolve()
    if not job_dir.is_relative_to(OUTPUT_ROOT.resolve()):
        raise HTTPException(status_code=404, detail="Not found")
    metadata = read_metadata(job_dir)
    if metadata is None or metadata.get("state") != "complete":
        raise HTTPException(status_code=404, detail="Not found")
    if metadata["expires_at"] <= time.time():
        raise HTTPException(status_code=410, detail="Las descargas han caducado.")
    target = (job_dir / "artifacts" / filename).resolve()
    if not target.is_file() or not target.is_relative_to(job_dir) or filename not in {
        "result.xlsx", "result.docx", "result.txt", "document.ir.json", "warnings.json",
    }:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target, filename=filename)


def main() -> None:
    import uvicorn

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    host, port = settings.host, settings.port
    print(f"PDF Converter (F0 local review UI) - abre http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
