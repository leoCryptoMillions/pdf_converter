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


# Per-cell layout enrichment (raw.within_bbox + positioned_lines + cell_runs +
# detect_fill, below) scans the whole page's objects on every call with no
# spatial index, so its cost grows with the page's total object count as well
# as the cell count - measured close to quadratic in cell count alone, i.e.
# roughly quartic in a square table's side length (a 75x75/5625-cell ruled
# table took ~100s for this loop alone, exceeding apps/conversion_isolation.py's
# 90s hard production timeout before export_xlsx's own VISUAL_GRID_TOO_DENSE
# fallback could ever run). Skipping the enrichment above this limit keeps
# extraction inside that budget so the graceful, warning-bearing degrade is
# actually reachable instead of an opaque timeout kill. Basic cell content
# (already extracted via found.extract() before this limit is checked) and
# row/col span (cheap, independent of page object count) are unaffected.
LAYOUT_ENRICHMENT_CELL_LIMIT = 2500


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
    from packages.converters.layout import (
        LayoutAssets, cell_runs, detect_fill, inside, positioned_lines, refine_tables,
    )
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
                # Matches the table-cell tolerance fix below: pdfplumber's
                # default x_tolerance=3 misses real word gaps in PDFs with no
                # explicit space glyph, merging words in the base extracted
                # text (used by TXT export, the preview and XLSX's full-text
                # sheet alike).
                text = raw.extract_text(x_tolerance=1) or ""
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
                blank_page = not (text.strip() or raw.chars or raw.images or raw.rects or raw.curves or raw.lines or raw.annots)
                if blank_page:
                    page.metadata['blank_page'] = True
                    page.warnings.append(ContentWarning(level='info', code='EMPTY_PAGE',
                        message='No text, graphics, images or annotations detected on this page.', page_number=number))
                if not text.strip() and not blank_page:
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
                found_tables = raw.find_tables()
                if preserve_layout:
                    found_tables, refined = refine_tables(raw, found_tables)
                    if refined:
                        page.metadata['table_strategy'] = 'lines_without_decorative_fills'
                        page.metadata['refined_tables'] = refined
                        page.warnings.append(warning('TABLE_DECORATION_FILTERED',
                            'Decorative fill edges were excluded from the table grid; extracted character multiplicities were preserved.', number))
                for index, found in enumerate(found_tables, 1):
                    # pdfplumber's own default (x_tolerance=3) misses real word
                    # gaps in small-font tables with no explicit space glyphs
                    # (seen on a real SAT "Constancia de Situacion Fiscal":
                    # 8pt text, ~2.2pt word gaps) and merges words together.
                    rows = found.extract(x_tolerance=1)
                    if not rows:
                        continue
                    cells = []
                    # pdfplumber's Table.rows/.columns are plain @property, not
                    # cached - found.rows[r] alone recomputes the *entire* grid
                    # from scratch. Evaluating it once per (r, c) pair inside
                    # this nested loop (as a naive `found.rows[r].cells[c]`
                    # would) makes grid construction itself O(cells^2); a
                    # 75x75 table measured this one line alone costing ~19s of
                    # a ~100s total. Reading the property once removes that
                    # self-inflicted quadratic cost with no behavior change -
                    # found.rows is a pure, deterministic computation from the
                    # table's own immutable structure.
                    found_rows = found.rows
                    for r, values in enumerate(rows):
                        for c, value in enumerate(values):
                            bbox = found_rows[r].cells[c]
                            cell = Cell(content=value or "", row_index=r, col_index=c,
                                        extraction_method="direct",
                                        original_source=Rectangle(x0=bbox[0], y0=bbox[1], x1=bbox[2], y1=bbox[3]) if bbox else None)
                            if value is None or bbox is None:
                                cell.warnings.append(warning("MISSING_OR_MERGED_CELL", "Cell may be empty or merged; check the source.", number))
                            elif "\n" in value:
                                # The source PDF may lack a row-dividing line this
                                # cell's neighbours have (seen on a real quotation:
                                # a SUBTOTAL/IVA/TOTAL block with no internal lines
                                # under its label column), collapsing what should
                                # be several rows into one cell here.
                                cell.warnings.append(warning("MULTI_LINE_CELL_MAY_SPAN_ROWS",
                                    "Cell has multiple lines; the source may have more rows than detected here. Compare with the original.", number))
                            cells.append(cell)
                    x0, y0, x1, y1 = found.bbox
                    page.tables.append(Table(id=f"p{number}_t{index}", page_number=number,
                                             location=Rectangle(x0=x0, y0=y0, x1=x1, y1=y1),
                                             rows=len(rows), columns=max(map(len, rows)), cells=cells,
                                             column_widths=[col.bbox[2] - col.bbox[0] for col in found.columns],
                                             row_heights=[row.bbox[3] - row.bbox[1] for row in found_rows],
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
                        skip_enrichment = len(table.cells) > LAYOUT_ENRICHMENT_CELL_LIMIT
                        if skip_enrichment:
                            table.warnings.append(warning('TABLE_LAYOUT_ENRICHMENT_SKIPPED',
                                f'Table has {len(table.cells)} cells, above the {LAYOUT_ENRICHMENT_CELL_LIMIT}-cell '
                                'processing budget; per-cell highlight colors and styled runs were not computed to '
                                'stay within the conversion time limit. Cell text content is unaffected; compare '
                                'highlight bands and run styling with the source PDF.', number))
                        for cell in table.cells:
                            if cell.original_source is None:
                                continue
                            box = cell.original_source
                            cell.col_span = max(1, sum(box.x0 < x <= box.x1 for x in xs))
                            cell.row_span = max(1, sum(box.y0 < y <= box.y1 for y in ys))
                            if skip_enrichment:
                                continue
                            # Extract each cell independently. A page-wide
                            # line can straddle adjacent cells and lose the
                            # smaller cell's font/style when split by centre.
                            region = raw.within_bbox((box.x0 + raw.bbox[0], box.y0 + raw.bbox[1],
                                                      box.x1 + raw.bbox[0], box.y1 + raw.bbox[1]), strict=False)
                            cell.fill_color = detect_fill(raw.rects, box.x0 + raw.bbox[0], box.y0 + raw.bbox[1],
                                                           box.x1 + raw.bbox[0], box.y1 + raw.bbox[1])
                            cell_lines = positioned_lines(region, origin=raw.bbox[:2])
                            cell.runs = cell_runs(cell_lines, cell.content)
                            if cell_lines:
                                cell.padding_left = max(0, min(b.location.x0 for b in cell_lines) - box.x0)
                                cell.padding_top = max(0, min(b.location.y0 for b in cell_lines) - box.y0)
                    for index, line in enumerate(lines, 1):
                        if any(inside(line.location, t.location) for t in page.tables):
                            continue
                        page.blocks.append(TextBlock(id=f"p{number}_b{index}", content=line.content,
                            runs=line.runs, page_number=number, reading_order=index,
                            extraction_method="direct", location=line.location,
                            fill_color=detect_fill(raw.rects, line.location.x0 + raw.bbox[0], line.location.y0 + raw.bbox[1],
                                                    line.location.x1 + raw.bbox[0], line.location.y1 + raw.bbox[1])))
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
