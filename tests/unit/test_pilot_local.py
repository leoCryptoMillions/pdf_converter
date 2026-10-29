"""Pilot acceptance checks must detect damaged outputs, not just readable ZIPs."""
from io import BytesIO

import pytest
from openpyxl import load_workbook
from reportlab.pdfgen import canvas

from benchmarks.pilot_local import check_exports
from packages.converters.digital import extract_digital
from packages.exporters.docx import export_docx
from packages.exporters.xlsx import export_xlsx


def artifacts_for(source):
    ir = extract_digital(source, preserve_layout=True)
    return ir, {"result.docx": export_docx(ir), "result.xlsx": export_xlsx(ir),
                "result.txt": ir.get_all_text().encode("utf-8")}


def test_pilot_validates_current_excel_and_edit_save_reopen(synthetic_invoice):
    ir, artifacts = artifacts_for(synthetic_invoice)
    checks = check_exports(ir, artifacts, synthetic_invoice)
    assert checks["passed"]
    assert checks["xlsx_full_text_matches_ir"]
    assert checks["python_word_edit_save_reopen"]
    assert checks["python_excel_edit_save_reopen"]


@pytest.mark.parametrize("damage", ["lost_text", "wrong_active_sheet", "missing_page"])
def test_pilot_rejects_damaged_excel_even_when_table_values_survive(synthetic_invoice, damage):
    ir, artifacts = artifacts_for(synthetic_invoice)
    workbook = load_workbook(BytesIO(artifacts["result.xlsx"]))
    if damage == "lost_text":
        workbook["Texto completo"]["A1"] = "LOST SOURCE TEXT"
    elif damage == "wrong_active_sheet":
        workbook.active = workbook.sheetnames.index("_Original")
    else:
        del workbook["Pagina_1"]
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    artifacts["result.xlsx"] = stream.getvalue()
    checks = check_exports(ir, artifacts, synthetic_invoice)
    assert checks["xlsx_cells_match_ir"]
    assert not checks["passed"]


def test_pilot_checks_full_text_for_document_without_tables(tmp_path):
    source = tmp_path / "letter.pdf"
    pdf = canvas.Canvas(str(source))
    pdf.drawString(50, 700, "Letter without any ruled table.")
    pdf.save()
    ir, artifacts = artifacts_for(source)
    assert not ir.get_all_tables()
    checks = check_exports(ir, artifacts, source)
    assert checks["xlsx_full_text_matches_ir"]
    assert checks["passed"]


def test_pilot_preserves_blank_page_and_excel_row_height_limit(tmp_path):
    source = tmp_path / "blank-between-pages.pdf"
    pdf = canvas.Canvas(str(source))
    pdf.drawString(50, 700, "First page")
    pdf.showPage()
    pdf.showPage()
    pdf.drawString(50, 700, "Third page")
    pdf.save()
    ir, artifacts = artifacts_for(source)
    assert len(ir.pages) == 3
    workbook = load_workbook(BytesIO(artifacts["result.xlsx"]))
    assert workbook.sheetnames[:3] == ["Pagina_1", "Pagina_2", "Pagina_3"]
    assert all(dimension.height <= 409.5 for dimension in workbook["Pagina_2"].row_dimensions.values())
    workbook.close()
    checks = check_exports(ir, artifacts, source)
    assert checks["xlsx_blank_source_pages"] == [2]
    assert checks["passed"]


def test_excel_recovers_observed_vector_fill_behind_white_text(tmp_path):
    from reportlab.lib.colors import HexColor, white, black

    source = tmp_path / "white-on-vector-panel.pdf"
    pdf = canvas.Canvas(str(source), pagesize=(300, 250))
    path = pdf.beginPath()
    path.moveTo(40, 100)
    path.lineTo(90, 100)  # Extra vertex keeps this a vector path, not a PDF rect operator.
    path.lineTo(140, 100)
    path.lineTo(140, 160)
    path.lineTo(40, 160)
    path.close()
    pdf.setFillColor(HexColor('#123456'))
    pdf.drawPath(path, fill=1, stroke=0)
    pdf.setStrokeColor(black)
    for y in (100, 130, 160):
        pdf.line(40, y, 240, y)
    for x in (40, 140, 240):
        pdf.line(x, 100, x, 160)
    pdf.setFont('Helvetica', 9)
    pdf.setFillColor(white)
    pdf.drawString(45, 140, 'WHITE LABEL')
    pdf.drawString(45, 110, 'SECOND LABEL')
    pdf.setFillColor(black)
    pdf.drawString(145, 140, 'Value A')
    pdf.drawString(145, 110, 'Value B')
    pdf.save()
    ir, artifacts = artifacts_for(source)
    # The source panel is a filled path rather than a PDF rect object.
    cell = next(c for t in ir.get_all_tables() for c in t.cells if c.content == 'WHITE LABEL')
    assert cell.fill_color is None
    workbook = load_workbook(BytesIO(artifacts['result.xlsx']))
    target = next(c for row in workbook.active for c in row if c.value == 'WHITE LABEL')
    assert target.font.color.rgb == 'FFFFFFFF'
    assert target.fill.fgColor.rgb == 'FF123456'
    workbook.close()
