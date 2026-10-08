from io import BytesIO
from pathlib import Path
import subprocess
import sys

from openpyxl import load_workbook
import pytest
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from benchmarks.common import character_error_rate, table_f1
from packages.converters.digital import PDFValidationError, extract_digital
from packages.exporters.xlsx import export_xlsx


@pytest.fixture
def digital_pdf(tmp_path):
    path = tmp_path / "table.pdf"
    rows = [["Identifier", "Quantity", "Amount", "Notes"],
            ["000123456789012345", "2", "$350.50", '=HYPERLINK("https://example.invalid")'],
            ["000123456789012345", "2", "$350.50", '=HYPERLINK("https://example.invalid")'],
            ["ABC", "012", "1.234,56", "@SUM(A1)"]]
    table = Table(rows, colWidths=[115, 55, 70, 240])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                               ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    SimpleDocTemplate(str(path)).build([table])
    return path, rows


def test_real_extraction_export_preserves_duplicates_ids_and_formulas(digital_pdf):
    source, expected = digital_pdf
    document = extract_digital(source)
    assert document.pages[0].text_coverage is None
    assert document.text_extraction_confidence is None
    assert document.has_warnings()
    table = document.get_all_tables()[0]
    assert table.rows == 4
    assert table.confidence is None
    wb = load_workbook(BytesIO(export_xlsx(document)), data_only=False)
    ws = wb["Table_1"]
    for r, row in enumerate(expected, 1):
        for c, text in enumerate(row, 1):
            assert ws.cell(r, c).value == text
            assert ws.cell(r, c).data_type == "s"
    assert len(wb["_Original"]["E"]) == 17
    assert {"_Origin", "_Original", "_Warnings"} <= set(wb.sheetnames)
    wb.close()


def test_numeric_types_are_explicit_and_ambiguous_values_stay_text(digital_pdf):
    document = extract_digital(digital_pdf[0])
    data = export_xlsx(document, numeric_columns={"p1_t1": {1: "integer", 2: "currency"}})
    wb = load_workbook(BytesIO(data), data_only=False)
    ws = wb["Table_1"]
    assert ws["A2"].value == "000123456789012345"
    assert ws["B2"].value == 2
    assert ws["C2"].value == 350.5
    assert ws["B4"].value == "012"
    assert ws["C4"].value == "1.234,56"
    assert wb["_Original"]["E8"].value == "$350.50"
    warnings = list(wb["_Warnings"].values)
    assert sum(row[0] == "NUMERIC_VALUE_KEPT_AS_TEXT" for row in warnings) == 2
    wb.close()


def test_excel_precision_guard(digital_pdf):
    document = extract_digital(digital_pdf[0])
    document.pages[0].tables[0].cells[5].content = "1234567890123456"
    wb = load_workbook(BytesIO(export_xlsx(document, numeric_columns={"p1_t1": {1: "integer"}})))
    assert wb["Table_1"]["B2"].value == "1234567890123456"
    wb.close()


def test_metadata_does_not_become_a_formula(digital_pdf):
    document = extract_digital(digital_pdf[0])
    document.engines_used[0].engine_version = "=1+1"
    document.pages[0].tables[0].id = "=2+2"
    wb = load_workbook(BytesIO(export_xlsx(document)), data_only=False)
    assert all(cell.data_type != "f" for sheet in wb for row in sheet for cell in row)
    wb.close()


@pytest.mark.parametrize("text", ["x" * 32768, "bad\x00text"], ids=["too_long", "control_character"])
def test_unrepresentable_excel_text_fails_instead_of_truncating(digital_pdf, text):
    document = extract_digital(digital_pdf[0])
    document.pages[0].tables[0].cells[0].content = text
    with pytest.raises(ValueError, match="losslessly"):
        export_xlsx(document)


def test_duplicate_cell_coordinates_rejected(digital_pdf):
    document = extract_digital(digital_pdf[0])
    table = document.pages[0].tables[0]
    table.cells.append(table.cells[0])
    with pytest.raises(ValueError, match="duplicate"):
        export_xlsx(document)


def test_docx_contains_editable_table_without_duplicate_text(digital_pdf):
    from docx import Document
    from packages.exporters.docx import export_docx

    document = extract_digital(digital_pdf[0])
    reopened = Document(BytesIO(export_docx(document)))
    assert len(reopened.tables) == 1
    assert reopened.tables[0].cell(1, 0).text == "000123456789012345"
    assert all("Identifier" not in paragraph.text for paragraph in reopened.paragraphs)
    reopened.tables[0].cell(1, 1).text = "Edited"
    output = BytesIO()
    reopened.save(output)
    assert Document(BytesIO(output.getvalue())).tables[0].cell(1, 1).text == "Edited"


def test_input_limits_and_signature(digital_pdf, tmp_path):
    with pytest.raises(PDFValidationError, match="size"):
        extract_digital(digital_pdf[0], max_bytes=10)
    with pytest.raises(PDFValidationError, match="page limit"):
        extract_digital(digital_pdf[0], max_pages=0)
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a pdf")
    with pytest.raises(PDFValidationError, match="signature"):
        extract_digital(invalid)
    invalid.write_bytes(b"%PDF-1.7\nbroken")
    with pytest.raises(PDFValidationError, match="parsed"):
        extract_digital(invalid)


def test_encrypted_pdf_rejected(digital_pdf, tmp_path):
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    writer.append(PdfReader(digital_pdf[0]))
    writer.encrypt("secret")
    path = tmp_path / "encrypted.pdf"
    writer.write(path)
    with pytest.raises(PDFValidationError):
        extract_digital(path)


def test_cli_outputs_and_refuses_overwrite(digital_pdf, tmp_path):
    output = tmp_path / "conversion"
    command = [sys.executable, "-m", "apps.convert", str(digital_pdf[0]), "--output", str(output),
               "--formats", "xlsx", "docx", "txt"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (output / "result.xlsx").is_file()
    assert (output / "result.docx").is_file()
    assert "Identifier" in (output / "result.txt").read_text(encoding="utf-8")
    assert (output / "summary.json").is_file()
    assert subprocess.run(command, capture_output=True).returncode == 1


@pytest.mark.parametrize("expected,actual,distance", [
    ("abc", "abc", 0), ("kitten", "sitting", 3), ("abab", "baba", 2),
    ("abc", "", 3), ("a", "bbbb", 4),
])
def test_exact_cer(expected, actual, distance):
    assert character_error_rate(expected, actual) == pytest.approx(distance / len(expected))


def test_table_metric_detects_missing_duplicate():
    score = table_f1([{"rows": [["A"], ["A"]]}], [[["A"]]])
    assert score["recall"] == 0.5
    assert score["f1"] == pytest.approx(2 / 3)


def test_draft_reference_is_not_scored(tmp_path, monkeypatch):
    import benchmarks.common as common

    (tmp_path / "draft.json").write_text('{"review_status": "draft"}', encoding="utf-8")
    monkeypatch.setattr(common, "GROUND_TRUTH_DIR", tmp_path)
    assert common.load_ground_truth("draft") is None


def test_reference_hash_mismatch_is_rejected(tmp_path, monkeypatch):
    import benchmarks.common as common

    (tmp_path / "local").mkdir()
    (tmp_path / "local" / "test.json").write_text(
        '{"review_status": "verified", "source_sha256": "wrong_hash"}', encoding="utf-8")
    (tmp_path / "source.pdf").write_bytes(b"different source")
    monkeypatch.setattr(common, "GROUND_TRUTH_DIR", tmp_path)
    monkeypatch.setattr(common, "CORPUS_DIR", tmp_path)
    row = common.ManifestRow("test", "source.pdf", "digital_simple_table", 1, "synthetic", True, True)
    monkeypatch.setattr(common, "load_manifest", lambda: [row])
    with pytest.raises(ValueError, match="hash mismatch"):
        common.load_ground_truth("test")


def test_reference_path_traversal_rejected():
    from benchmarks.common import load_ground_truth

    with pytest.raises(ValueError, match="Invalid reference ID"):
        load_ground_truth("../reference")


@pytest.mark.parametrize("pages", [[], [0], [-1], [2], [1, 1], [True]],
                         ids=["empty", "zero", "negative", "outside", "duplicate", "boolean"])
def test_invalid_selected_pages_rejected(digital_pdf, pages):
    with pytest.raises(PDFValidationError, match="selected pages"):
        extract_digital(digital_pdf[0], page_numbers=pages)


def test_page_selection_retains_original_page_number_and_source_count(tmp_path):
    from reportlab.pdfgen import canvas

    path = tmp_path / "two_pages.pdf"
    writer = canvas.Canvas(str(path))
    writer.drawString(72, 700, "First page")
    writer.showPage()
    writer.drawString(72, 700, "Second page")
    writer.save()
    document = extract_digital(path, page_numbers=[2])
    assert document.page_count == 2
    assert len(document.pages) == 1
    assert document.pages[0].page_number == 2
    assert document.pages[0].extracted_text == "Second page"
    assert document.extraction_options["selected_pages"] == [2]
    assert "First page" not in document.get_all_text()


def test_scoped_table_benchmark_passes_only_annotated_pages(digital_pdf, monkeypatch):
    import benchmarks.tables_benchmark as benchmark
    from benchmarks.common import ManifestRow

    row = ManifestRow("scoped", digital_pdf[0].name, "digital_complex_table", 19, "synthetic", True, True)
    monkeypatch.setattr(benchmark, "load_manifest", lambda: [row])
    monkeypatch.setattr(benchmark, "usable_rows", lambda rows, categories: (rows, []))
    monkeypatch.setattr(benchmark, "load_ground_truth", lambda ident: {
        "scope": "selected_pages_tables", "pages": [{"page_number": 19, "tables": [{"rows": [["Value"]]}]}]})
    received = []

    def extractor(path, page_numbers=None):
        received.append(page_numbers)
        return [[["Value"]]]

    monkeypatch.setattr(benchmark, "ENGINES", {"test": extractor})
    results, skipped = benchmark.run()
    assert received == [[19]]
    assert results[0].metrics["f1"] == 1
    assert results[0].metrics["reference_scope"] == "selected_pages_tables"


def test_full_document_ocr_does_not_score_partial_page_reference(monkeypatch):
    import benchmarks.ocr_benchmark as benchmark
    from benchmarks.common import ManifestRow

    row = ManifestRow("scoped", "source.pdf", "scanned_clean", 14, "synthetic", True, True)
    monkeypatch.setattr(benchmark, "load_manifest", lambda: [row])
    monkeypatch.setattr(benchmark, "usable_rows", lambda rows, categories: (rows, []))
    monkeypatch.setattr(benchmark, "load_ground_truth", lambda ident: {
        "scope": "selected_pages_text", "pages": [{"page_number": 1, "text": "Cover"}]})
    monkeypatch.setattr(benchmark, "ENGINES", {"test": lambda path: "Cover"})
    results, skipped = benchmark.run()
    assert results[0].metrics["cer"] is None
    assert "partial-document" in results[0].metrics["note"]


def test_ocr_pixel_limit_rejects_page_before_rasterization(digital_pdf):
    from benchmarks.validate_prototype import ocr_page_text

    with pytest.raises(ValueError, match="pixel budget"):
        ocr_page_text(digital_pdf[0], 1, max_pixels=1)


def test_independent_pdfium_word_baseline_preserves_editable_text(tmp_path):
    from reportlab.pdfgen import canvas
    from benchmarks.validate_prototype import pdfium_text_docx_baseline

    path = tmp_path / "text.pdf"
    writer = canvas.Canvas(str(path))
    writer.drawString(72, 700, "Expected text")
    writer.save()
    result = pdfium_text_docx_baseline(path, tmp_path / "baseline.docx", "Expected text")
    assert result["cer_whitespace_normalized"] == 0
    assert result["edit_save_reopen"] is True


@pytest.fixture
def segmented_document():
    from packages.document_ir.models import Cell, DocumentIR, Page, Rectangle, Table

    pages = []
    for number, top in [(1, 700), (2, 70)]:
        cells = [Cell(content=f"p{number}_{r}_{c}", row_index=r, col_index=c,
                      extraction_method="direct", original_source=Rectangle(
                          x0=72 + c * 100, x1=172 + c * 100, y0=top + r * 30, y1=top + (r + 1) * 30))
                 for r in range(2) for c in range(2)]
        table = Table(id=f"p{number}_t1", page_number=number, rows=2, columns=2,
                      cells=cells, extraction_method="direct", source_engine="test",
                      location=Rectangle(x0=72, x1=272, y0=top, y1=top + 60))
        pages.append(Page(page_number=number, width=612, height=792, classification="digital",
                          image_coverage=0, tables=[table]))
    return DocumentIR(document_id="test", source_filename="test.pdf", source_hash="test",
                      page_count=2, pages=pages, engines_used=[])


def test_continuity_links_preserve_rows_and_warn_idempotently(segmented_document):
    from packages.converters.continuity import link_table_continuations

    tables = segmented_document.get_all_tables()
    original = [c.content for t in tables for c in t.cells]
    link_table_continuations(segmented_document)
    link_table_continuations(segmented_document)
    assert tables[1].continuation_of == tables[0].id
    assert len(tables[1].warnings) == 2
    assert [c.content for t in tables for c in t.cells] == original
    wb = load_workbook(BytesIO(export_xlsx(segmented_document)))
    assert wb["Table_1"].max_row == 2
    assert wb["Table_2"].max_row == 2
    assert any("continuation candidate" in str(row[0]) for row in wb["_Origin"].values)
    wb.close()


@pytest.mark.parametrize("mismatch", ["gap", "geometry", "rotation", "edge", "span"])
def test_continuity_rejects_insufficient_evidence(segmented_document, mismatch):
    from packages.converters.continuity import link_table_continuations

    previous, current = segmented_document.pages
    if mismatch == "gap":
        current.page_number = 3
    elif mismatch == "geometry":
        for cell in current.tables[0].cells:
            cell.original_source.x0 += 15
            cell.original_source.x1 += 15
    elif mismatch == "rotation":
        current.rotation = 90
    elif mismatch == "edge":
        previous.tables[0].location.y1 = 400
    else:
        current.tables[0].cells[0].col_span = 2
    link_table_continuations(segmented_document)
    assert current.tables[0].continuation_of is None


def test_cost_projection_requires_actual_tariffs():
    from benchmarks.resource_benchmark import cost_scenarios

    unknown = cost_scenarios(1, pages=[3600])[0]
    assert unknown["compute_cost_estimate"] is None
    assert unknown["total_estimate"] is None
    priced = cost_scenarios(1, pages=[3600], hourly_rate=3, fixed_monthly=4)[0]
    assert priced["sequential_worker_hours"] == 1
    assert priced["total_estimate"] == 7


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf")])
def test_cost_projection_rejects_invalid_resource_measurements(seconds):
    from benchmarks.resource_benchmark import cost_scenarios

    with pytest.raises(ValueError):
        cost_scenarios(seconds)
