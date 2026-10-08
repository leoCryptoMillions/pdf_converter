"""Bounded local F0 extraction; no OCR and no invented quality scores."""
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
                    max_pages: int = 100, page_numbers: list[int] | None = None) -> DocumentIR:
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
                    page.warnings.append(warning("OCR_REQUIRED", "Page has no extractable text; OCR was not run.", number))
                if raw.images:
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
                                             extraction_method="direct", source_engine="pdfplumber"))
                # Retain lines outside tables, ordered geometrically for DOCX.
                for index, line in enumerate(raw.extract_text_lines(), 1):
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
    document = DocumentIR(document_id=digest.hexdigest()[:32], source_filename=source.name,
                      source_hash=digest.hexdigest(), page_count=total_pages, pages=pages,
                      engines_used=[EngineConfig(engine_name="pdfplumber", engine_version=pdfplumber.__version__)],
                      extraction_options={"ocr": False, "table_strategy": "lines", "max_pages": max_pages,
                                          "selected_pages": sorted(selected)},
                      has_meaningful_content=any(p.extracted_text.strip() for p in pages),
                      total_processing_time_seconds=time.monotonic() - started,
                      warnings=[warning("UNVALIDATED_EXTRACTION", "Extraction quality has not been verified against a reference.", 1)])
    from packages.converters.continuity import link_table_continuations
    link_table_continuations(document)
    return document
