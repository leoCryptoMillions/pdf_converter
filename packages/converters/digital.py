"""Bounded local F0 extraction; no invented quality scores.

OCR is off by default (see docs/PROTOTIPO_F0.md) and only runs for pages
with no extractable digital text when `ocr=True` is passed; routing to
needs_review then follows DEC-04 (packages/converters/ocr.py).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import time

import pdfplumber

from packages.document_ir.models import (
    Cell, ContentWarning, DocumentIR, EngineConfig, Page, Rectangle, Table, TextBlock,
)


class PDFValidationError(ValueError):
    """Input cannot be processed within the prototype's contract."""


def warning(code: str, message: str, page: int) -> ContentWarning:
    return ContentWarning(level="warning", code=code, message=message, page_number=page)


def extract_digital(source: Path, *, max_bytes: int = 25 * 1024 * 1024,
                    max_pages: int = 100, page_numbers: list[int] | None = None,
                    ocr: bool = False, preserve_layout: bool = True) -> DocumentIR:
    source = Path(source)
    if source.stat().st_size > max_bytes:
        raise PDFValidationError("PDF exceeds size limit")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise PDFValidationError("Invalid PDF signature")
        stream.seek(0)
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    started = time.monotonic()
    from packages.converters.layout import LayoutAssets, cell_runs, inside, positioned_lines
    assets = LayoutAssets(source)
    try:
        with pdfplumber.open(source) as pdf:
            # Reject encrypted inputs even if they use an empty user password.
            if pdf.doc.encryption:
                raise PDFValidationError("Encrypted PDFs are unsupported")
            if not 0 < len(pdf.pages) <= max_pages:
                raise PDFValidationError("PDF exceeds page limit or has no pages")
            total_pages = len(pdf.pages)
            selected = list(range(1, total_pages + 1)) if page_numbers is None else page_numbers
            if (not selected or len(selected) != len(set(selected)) or
                any(type(number) is not int or not 1 <= number <= total_pages for number in selected)):
                raise PDFValidationError("Invalid selected pages")
            pages = []
            for number in sorted(selected):
                raw = pdf.pages[number - 1]
                text = raw.extract_text() or ""
                page = Page(page_number=number, width=raw.width, height=raw.height,
                            rotation=raw.rotation,
                            classification="mixed" if text and raw.images else
                            "digital" if text else "scanned",
                            image_coverage=min(1.0, sum(
                                max(0, im["x1"] - im["x0"]) * max(0, im["bottom"] - im["top"])
                                for im in raw.images) / (raw.width * raw.height)),
                            extracted_text=text,
                            metadata={"coordinate_system": "top-left, PDF points",
                                      "text_coverage_measured": False})
                if not text.strip():
                    if ocr:
                        from packages.converters.ocr import OCRUnavailableError, classify_ocr_result, ocr_page
                        try:
                            ocr_text, confidence = ocr_page(source, number)
                        except OCRUnavailableError as exc:
                            page.warnings.append(warning("OCR_FAILED", f"OCR could not run: {exc}", number))
                        else:
                            page.extracted_text = ocr_text
                            needs_review, ocr_warning = classify_ocr_result(number, confidence)
                            page.metadata["ocr_mean_confidence"] = confidence
                            page.metadata["ocr_needs_review"] = needs_review
                            page.warnings.append(ocr_warning)
                            if ocr_text.strip():
                                page.blocks.append(TextBlock(
                                    id=f"p{number}_ocr", content=ocr_text, page_number=number,
                                    reading_order=1, extraction_method="ocr", confidence=confidence,
                                    location=Rectangle(x0=0, y0=0, x1=raw.width, y1=raw.height)))
                    else:
                        page.warnings.append(warning("OCR_REQUIRED", "Page has no extractable text; OCR was not run.", number))
                if raw.images and not preserve_layout:
                    page.warnings.append(warning("IMAGES_NOT_EXTRACTED", "Embedded images are not exported by this F0 prototype.", number))
                for index, found in enumerate(raw.find_tables(), 1):
                    rows = found.extract()
                    if not rows:
                        continue
                    cells = []
                    for r, values in enumerate(rows):
                        for c, value in enumerate(values):
                            bbox = found.rows[r].cells[c]
                            cell = Cell(content=value or "", row_index=r, col_index=c,
                                        extraction_method="direct",
                                        original_source=Rectangle(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]) if bbox else None)
                            if value is None or bbox is None:
                                cell.warnings.append(warning("MISSING_OR_MERGED_CELL", "Cell may be empty or merged; check the source.", number))
                            cells.append(cell)
                    x0, y0, x1, y1 = found.bbox
                    page.tables.append(Table(id=f"p{number}_t{index}", page_number=number,
                                             location=Rectangle(x0=x0, y0=y0, x1=x1, y1=y1),
                                             rows=len(rows), columns=max(map(len, rows)), cells=cells,
                                             column_widths=[col.bbox[2] - col.bbox[0] for col in found.columns],
                                             row_heights=[row.bbox[3] - row.bbox[1] for row in found.rows],
                                             extraction_method="direct", source_engine="pdfplumber"))
                if preserve_layout:
                    lines = positioned_lines(raw)
                    for table in page.tables:
                        # Normalize every layout coordinate to this page's top-left.
                        for box in [table.location, *(c.original_source for c in table.cells if c.original_source)]:
                            box.x0 -= raw.bbox[0]
                            box.x1 -= raw.bbox[0]
                            box.y0 -= raw.bbox[1]
                            box.y1 -= raw.bbox[1]
                        table.text_lines = [line for line in lines if inside(line.location, table.location)]
                        xs = sorted({v for c in table.cells if c.original_source
                                     for v in (c.original_source.x0, c.original_source.x1)})
                        ys = sorted({v for c in table.cells if c.original_source
                                     for v in (c.original_source.y0, c.original_source.y1)})
                        # A merged header makes found.columns[0].bbox span
                        # several columns. Recover the actual grid boundaries.
                        if len(xs) == table.columns + 1:
                            table.column_widths = [b - a for a, b in zip(xs, xs[1:])]
                        if len(ys) == table.rows + 1:
                            table.row_heights = [b - a for a, b in zip(ys, ys[1:])]
                        for cell in table.cells:
                            if cell.original_source is None:
                                continue
                            box = cell.original_source
                            cell_lines = [line for line in table.text_lines if inside(line.location, box)]
                            cell.runs = cell_runs(cell_lines, cell.content)
                            cell.col_span = max(1, sum(box.x0 < x <= box.x1 for x in xs))
                            cell.row_span = max(1, sum(box.y0 < y <= box.y1 for y in ys))
                            if cell_lines:
                                cell.padding_left = max(0, min(b.location.x0 for b in cell_lines) - box.x0)
                                cell.padding_top = max(0, min(b.location.y0 for b in cell_lines) - box.y0)
                    for index, line in enumerate(lines, 1):
                        if any(inside(line.location, t.location) for t in page.tables):
                            continue
                        page.blocks.append(TextBlock(id=f"p{number}_b{index}", content=line.content,
                            runs=line.runs, page_number=number, reading_order=index,
                            extraction_method="direct", location=line.location))
                    assets.extract(raw, page)
                    page.metadata['word_layout'] = 'positioned-v1' if text.strip() else 'ocr-flow-v1'
                    page.warnings.append(warning('DOCX_LAYOUT_APPROXIMATE',
                        'Word preserves observed typography and geometry approximately; fonts and editing may change pagination.', number))
                    if any(not c.get('upright', True) for c in raw.chars):
                        page.warnings.append(warning('ROTATED_TEXT_LAYOUT',
                            'Some text is rotated; verify its orientation in Word.', number))
                # Retain lines outside tables, ordered geometrically for DOCX.
                for index, line in enumerate(raw.extract_text_lines() if not preserve_layout else [], 1):
                    cx, cy = (line["x0"] + line["x1"]) / 2, (line["top"] + line["bottom"]) / 2
                    if any(t.location.x0 <= cx <= t.location.x1 and
                           t.location.y0 <= cy <= t.location.y1 for t in page.tables):
                        continue
                    page.blocks.append(TextBlock(id=f"p{number}_b{index}", content=line["text"],
                        page_number=number, reading_order=index, extraction_method="direct",
                        location=Rectangle(x0=line["x0"], y0=line["top"], x1=line["x1"], y1=line["bottom"])))
                raw.close()
                pages.append(page)
    except PDFValidationError:
        raise
    except Exception as exc:
        raise PDFValidationError("PDF could not be parsed") from exc
    finally:
        assets.close()
    document = DocumentIR(document_id=digest.hexdigest()[:32], source_filename=source.name,
                      source_hash=digest.hexdigest(), page_count=total_pages, pages=pages,
                      engines_used=[EngineConfig(engine_name="pdfplumber", engine_version=pdfplumber.__version__)],
                      extraction_options={"ocr": ocr, "table_strategy": "lines", "max_pages": max_pages,
                                          "selected_pages": sorted(selected), "preserve_layout": preserve_layout},
                      has_meaningful_content=any(p.extracted_text.strip() for p in pages),
                      total_processing_time_seconds=time.monotonic() - started,
                      ocr_enabled=ocr, ocr_languages=["spa", "eng"] if ocr else [],
                      warnings=[warning("UNVALIDATED_EXTRACTION", "Extraction quality has not been verified against a reference.", 1)])
    if document.get_all_images() and assets.engine_version:
        document.engines_used.append(EngineConfig(engine_name='pypdfium2',
            engine_version=assets.engine_version,
            parameters={'pdfium_version': assets.pdfium_version,
                        'purpose': 'non-text layout assets', 'max_dpi': 180}))
    from packages.converters.continuity import link_table_continuations
    link_table_continuations(document)
    return document
