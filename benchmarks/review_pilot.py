"""Compare installed Office renders and prepare a private pilot review page.

python -m benchmarks.review_pilot --output .generated/mvp-pilot/run-01
Run benchmarks/render_pilot.ps1 first. Human decisions stay in revision.csv.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import html
import json
from pathlib import Path
import re

from docx import Document
import pypdfium2 as pdfium

from benchmarks.validate_word import content_comparison, pdfium_text, word_text
from packages.document_ir.models import DocumentIR


def render_pages(source: Path, directory: Path, prefix: str) -> int:
    with pdfium.PdfDocument(source) as pdf:
        for number in range(len(pdf)):
            page = pdf[number]
            try:
                bitmap = page.render(scale=1.5)
                try:
                    bitmap.to_pil().save(directory / f"{prefix}-{number + 1}.png")
                finally:
                    bitmap.close()
            finally:
                page.close()
        return len(pdf)


def write_review(report: dict, output: Path) -> None:
    sections = []
    for case in report["cases"]:
        identifier = html.escape(case["id"], quote=True)
        figures = []
        for number in range(1, max(case["pages"], case["office"]["word_rendered_pages"]) + 1):
            columns = []
            for prefix, label in (("source", "PDF original"), ("word", "Microsoft Word"), ("excel", "Microsoft Excel")):
                relative = f"{identifier}/{prefix}-{number}.png"
                image = (f'<a href="{relative}" target="_blank" rel="noopener"><img src="{relative}" '
                         f'alt="{label}, página {number}" loading="lazy"></a>'
                         if (output / case["id"] / f"{prefix}-{number}.png").is_file()
                         else '<p>No hay una página correspondiente.</p>')
                columns.append(f'<figure><figcaption>{label}</figcaption>{image}</figure>')
            figures.append(f'<h3>Página {number}</h3><div class="pair">{"".join(columns)}</div>')
        downloads = " · ".join(f'<a href="{identifier}/{filename}">{label}</a>' for filename, label in
            (("source.pdf", "PDF original"), ("result.docx", "Word"), ("result.xlsx", "Excel"),
             ("edited-in-word.docx", "Copia editada en Word"), ("edited-in-excel.xlsx", "Copia editada en Excel")))
        status = "Pasan" if case["technical_checks_passed"] else "Requieren atención"
        sections.append(f'<details open><summary>{identifier} · {case["pages"]} páginas</summary>'
                        f'<p>{downloads}</p><p>Comprobaciones técnicas: <strong>{status}</strong>. '
                        'Decisión humana: <strong>pendiente</strong>.</p>' + ''.join(figures) + '</details>')
    document = '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión del piloto PDF / Word / Excel</title><style>
body{font-family:system-ui,sans-serif;margin:24px;background:#eef2f1;color:#192e2b}main{max-width:1800px;margin:auto}
h1{font-size:28px}details{background:white;border:1px solid #c7d4cf;border-radius:12px;padding:20px;margin:24px 0}
summary{font-weight:700;cursor:pointer;padding:12px}a{color:#146c55}a:focus-visible,summary:focus-visible{outline:3px solid #146c55;outline-offset:4px}
.pair{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}figure{margin:0}figcaption{padding:12px;font-weight:600}
img{width:100%;height:auto;display:block;border:1px solid #c7d4cf;box-sizing:border-box}@media(max-width:800px){.pair{grid-template-columns:1fr}body{margin:12px}}
</style><main><h1>Piloto: PDF / Word / Excel</h1><p>Archivos privados de este equipo. Compara texto y orden, cifras, tablas y apariencia.
Pulsa una imagen para verla ampliada. Las comprobaciones técnicas no sustituyen la revisión humana.</p>
<p><a href="revision.csv">Abrir lista de aceptación</a> · <a href="report.json">Informe técnico</a></p>
<p>Revisa los avisos de los archivos. Registra tu decisión, nombre y notas en revision.csv; las copias de edición son pruebas técnicas.</p>
''' + ''.join(sections) + '</main></html>'
    (output / "review.html").write_text(document, encoding="utf-8")


def compare(output: Path) -> dict:
    output = output.resolve()
    private_root = (Path(__file__).resolve().parents[1] / ".generated").resolve()
    if not output.is_relative_to(private_root) or output == private_root:
        raise ValueError("Review directory must be inside .generated/")
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    pending = [case["id"] for case in report["cases"]
               if not all((output / case["id"] / name).is_file()
                          for name in ("word-runtime.json", "excel-runtime.json"))]
    if pending:
        raise ValueError("Office render/edit checks are not complete for: " + ", ".join(pending))
    for case in report["cases"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", case["id"]):
            raise ValueError("Invalid case ID")
        directory = output / case["id"]
        ir = DocumentIR.model_validate_json((directory / "document.ir.json").read_bytes())
        word_runtime = json.loads((directory / "word-runtime.json").read_text(encoding="utf-8-sig"))
        excel_runtime = json.loads((directory / "excel-runtime.json").read_text(encoding="utf-8-sig"))
        source_pages = render_pages(directory / "source.pdf", directory, "source")
        word_pages = render_pages(directory / "word-render.pdf", directory, "word")
        rendered_word = content_comparison(word_text(Document(directory / "result.docx")),
                                           pdfium_text(directory / "word-render.pdf"))
        excel_pages = []
        with pdfium.PdfDocument(directory / "source.pdf") as source_pdf:
            for page in ir.pages:
                number = page.page_number
                excel_pdf = directory / f"excel-page-{number}.pdf"
                count = render_pages(excel_pdf, directory, f"excel-temp-{number}")
                # Each page sheet is expected to print to exactly one PDF page.
                (directory / f"excel-temp-{number}-1.png").replace(directory / f"excel-{number}.png")
                source_page = source_pdf[number - 1]
                try:
                    text_page = source_page.get_textpage()
                    try:
                        expected = text_page.get_text_range()
                    finally:
                        text_page.close()
                finally:
                    source_page.close()
                comparison = content_comparison(expected, pdfium_text(excel_pdf))
                excel_pages.append({"page": number, "rendered_pages": count, "source_vs_excel": comparison})
        office = {
            "word_rendered_pages": word_pages, "word_page_count_matches": word_pages == source_pages,
            "word_edit_save_reopen": word_runtime["paragraph_edit_save_reopen"],
            "word_table_edit_save_reopen": word_runtime["table_edit_save_reopen"],
            "word_rendered_text": rendered_word,
            "excel_edit_save_reopen": excel_runtime["edit_save_reopen"],
            "excel_pages": excel_pages,
        }
        office["checks_passed"] = all((office["word_page_count_matches"], office["word_edit_save_reopen"],
            office["word_table_edit_save_reopen"] is not False, office["excel_edit_save_reopen"],
            rendered_word["exact_character_multiset"],
            all(p["rendered_pages"] == 1 and p["source_vs_excel"]["exact_character_multiset"] for p in excel_pages)))
        case["office"] = office
        case["technical_checks_passed"] = bool(case.get("checks", {}).get("passed")) and office["checks_passed"]
        case["artifact_sha256"] = {name: sha256((directory / name).read_bytes()).hexdigest()
                                   for name in ("source.pdf", "result.docx", "result.xlsx", "document.ir.json")}
        print(json.dumps({"id": case["id"], "technical_checks_passed": case["technical_checks_passed"],
                          "word_pages": word_pages, "excel_pages": len(excel_pages),
                          "word_render_missing": rendered_word["missing_characters"],
                          "excel_render_missing": sum(p["source_vs_excel"]["missing_characters"] for p in excel_pages)}))
    report["technical_checks_passed"] = all(case["technical_checks_passed"] for case in report["cases"])
    report["reviewer_script_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    checklist = output / "revision.csv"
    with checklist.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    statuses = {case["id"]: "pass" if case["technical_checks_passed"] else "review" for case in report["cases"]}
    for row in rows:
        row["automated_checks"] = statuses[row["id"]]
    with checklist.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_review(report, output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Review could not be prepared: {exc}\n")
    if not result["technical_checks_passed"]:
        parser.exit(1, "Some Office render checks need attention; see report.json\n")
