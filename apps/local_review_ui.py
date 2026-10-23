"""Local, single-user web wrapper around the F0 CLI (apps/convert.py).

Not the F1 web app: no auth, no database, no queue, no multi-tenancy, no
retention/TTL policy. It runs conversions synchronously, in-process, and is
meant to be started on your own machine and opened at 127.0.0.1 only -
docs/PROTOTIPO_F0.md explicitly defers the real "flujo web con usuarios,
trabajos, storage y cola" to F1. This exists purely so a user can drag a PDF
into a browser instead of typing CLI flags; it calls the exact same
extraction/export functions apps/convert.py does.

Run: python -m apps.local_review_ui
Then open http://127.0.0.1:8420/
"""
from __future__ import annotations

import html
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST

from packages.converters.digital import PDFValidationError, extract_digital

OUTPUT_ROOT = Path(".generated/web_ui")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # Matches extract_digital's own default limit.
ALLOWED_FORMATS = {"xlsx", "docx", "txt"}

app = FastAPI(title="PDF Converter - F0 local review UI", docs_url=None, redoc_url=None)


PAGE_SHELL = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>PDF Converter (F0 - local)</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; color: #1a1a1a; }}
h1 {{ font-size: 1.25rem; }}
fieldset {{ border: 1px solid #ccc; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
label {{ display: block; margin: 8px 0 4px; }}
.warn {{ background: #fff8e1; border: 1px solid #e0c200; border-radius: 8px; padding: 12px; margin-bottom: 16px; }}
.error {{ background: #fdecea; border: 1px solid #e04040; border-radius: 8px; padding: 12px; margin-bottom: 16px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
td, th {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; font-size: 0.9rem; }}
button {{ padding: 8px 16px; font-size: 1rem; cursor: pointer; }}
a.download {{ display: inline-block; margin: 4px 8px 4px 0; }}
</style></head><body>
<h1>PDF Converter - revisión local (prototipo F0)</h1>
<p class="warn">Prototipo F0: solo para uso local en tu máquina, un documento
a la vez. No hay cuentas, ni cola, ni borrado automático de resultados
(quedan en <code>.generated/web_ui/</code>). Toda conversión termina en
<code>needs_review</code> a propósito.</p>
{body}
</body></html>"""


def render_form(error: str | None = None) -> str:
    error_html = f'<div class="error">{html.escape(error)}</div>' if error else ""
    return PAGE_SHELL.format(body=f"""
{error_html}
<form action="/convert" method="post" enctype="multipart/form-data">
  <fieldset>
    <label for="file">Archivo PDF (máx. 25 MB)</label>
    <input type="file" id="file" name="file" accept="application/pdf" required>

    <label for="pages">Páginas (opcional, 1-indexado, separadas por coma; vacío = todas)</label>
    <input type="text" id="pages" name="pages" placeholder="1,3">

    <label><input type="checkbox" name="formats" value="xlsx" checked> XLSX</label>
    <label><input type="checkbox" name="formats" value="docx"> DOCX</label>
    <label><input type="checkbox" name="formats" value="txt" checked> TXT</label>

    <label><input type="checkbox" name="ocr" value="1"> Ejecutar OCR en páginas sin texto (Tesseract; más lento)</label>
  </fieldset>
  <button type="submit">Convertir</button>
</form>
""")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render_form()


@app.post("/convert", response_class=HTMLResponse)
async def convert(
    file: UploadFile,
    formats: list[str] = Form(default=["xlsx"]),
    pages: str = Form(default=""),
    ocr: str = Form(default=""),
) -> HTMLResponse:
    selected_formats = {f for f in formats if f in ALLOWED_FORMATS}
    if not selected_formats:
        return HTMLResponse(render_form("Selecciona al menos un formato de salida."), status_code=HTTP_400_BAD_REQUEST)

    page_numbers = None
    if pages.strip():
        try:
            page_numbers = [int(p.strip()) for p in pages.split(",") if p.strip()]
        except ValueError:
            return HTMLResponse(render_form("Páginas inválidas: usa números separados por coma, ej. 1,3."),
                                 status_code=HTTP_400_BAD_REQUEST)

    body = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(body) > MAX_UPLOAD_BYTES:
        return HTMLResponse(render_form(f"El archivo excede el límite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."),
                             status_code=HTTP_400_BAD_REQUEST)

    job_id = uuid.uuid4().hex
    job_dir = OUTPUT_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    # Server-generated name only; the original filename is never used for I/O.
    source_path = job_dir / "source.pdf"
    source_path.write_bytes(body)

    try:
        document = extract_digital(source_path, page_numbers=page_numbers, ocr=bool(ocr))
    except PDFValidationError as exc:
        return HTMLResponse(render_form(f"Conversión falló: {exc}"), status_code=HTTP_400_BAD_REQUEST)

    artifacts: dict[str, bytes] = {"document.ir.json": document.model_dump_json(indent=2).encode("utf-8")}
    if "xlsx" in selected_formats:
        from packages.exporters.xlsx import export_xlsx
        artifacts["result.xlsx"] = export_xlsx(document)
    if "docx" in selected_formats:
        from packages.exporters.docx import export_docx
        artifacts["result.docx"] = export_docx(document)
    if "txt" in selected_formats:
        artifacts["result.txt"] = document.get_all_text().encode("utf-8")

    for name, data in artifacts.items():
        (job_dir / name).write_bytes(data)

    warnings = document.warnings + [w for p in document.pages for w in p.warnings]
    links = "".join(f'<a class="download" href="/download/{job_id}/{name}">{html.escape(name)}</a>'
                     for name in artifacts if name != "document.ir.json")
    links += f'<a class="download" href="/download/{job_id}/document.ir.json">document.ir.json</a>'
    rows = "".join(f"<tr><td>{w.page_number}</td><td>{html.escape(w.code)}</td><td>{html.escape(w.message)}</td></tr>"
                    for w in warnings)
    body_html = f"""
<div class="warn">Estado: <strong>needs_review</strong> &middot;
{document.page_count} página(s) en el PDF, {len(document.pages)} procesada(s) &middot;
{len(document.get_all_tables())} tabla(s) detectada(s)</div>
<p>{links}</p>
<h2>Advertencias ({len(warnings)})</h2>
<table><tr><th>Página</th><th>Código</th><th>Mensaje</th></tr>{rows}</table>
<p><a href="/">&larr; Convertir otro archivo</a></p>
"""
    return HTMLResponse(PAGE_SHELL.format(body=body_html))


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
    print("PDF Converter (F0 local review UI) - abre http://127.0.0.1:8420/")
    uvicorn.run(app, host="127.0.0.1", port=8420)


if __name__ == "__main__":
    main()
