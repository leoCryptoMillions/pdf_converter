"""Minimal, opt-in OCR for pages with no extractable digital text (F0 scope).

The F0 CLI prototype does not run OCR by default (see docs/PROTOTIPO_F0.md);
this module only activates when `extract_digital(..., ocr=True)` is passed.
It implements the routing decided in DEC-04 (docs/AVANCE.md, 2026-10-20):

- No numeric accuracy threshold is validated for cover-like pages. Across
  14 preprocessing experiments, page 1 of the one scanned sample exercised
  in benchmarks (docs/PROTOTIPO_F0.md) stayed at 3.723% CER, above the 2%
  gate, while page 3 (continuous text) passed at 0.968%. Rather than average
  the two or invent a threshold for the failing case, page 1 of any
  OCR'd document is always routed to needs_review. This is a positional
  heuristic (page_number == 1), not a visual one: it matches the exact case
  that was measured, and it knowingly misclassifies covers that are not
  page 1, or documents with a multi-page cover.
- Continuous-text pages are routed on Tesseract's own mean word confidence
  (an engine-provided, non-fabricated metric), using the same 0.85 floor
  CLAUDE.md's own ContentWarning example already documents for
  "LOW_OCR_CONFIDENCE" - this is not a new invented number.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

from packages.document_ir.models import ContentWarning

OCR_LANGUAGES = "spa+eng"
OCR_PSM = "3"  # Best validated option for both page types (docs/PROTOTIPO_F0.md).
MIN_WORD_CONFIDENCE = 0.85  # Matches CLAUDE.md's own ContentWarning example.
OCR_TIMEOUT_SECONDS = 180  # Matches CLAUDE.md's "OCR: 180 seconds per page max".

_LOCAL_TESSDATA = Path(__file__).resolve().parents[2] / "benchmarks" / ".tessdata"
if _LOCAL_TESSDATA.is_dir():
    os.environ.setdefault("TESSDATA_PREFIX", str(_LOCAL_TESSDATA))

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
_POPPLER_GLOB_CANDIDATES = [
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages/*Poppler*/poppler-*/Library/bin"),
]


class OCRUnavailableError(RuntimeError):
    """Tesseract/poppler are missing, unreachable, or failed on this page."""


def _configure_windows_binaries() -> str | None:
    """Point pytesseract at a known winget tesseract.exe and return a poppler
    bin dir for pdf2image, mirroring benchmarks/ocr_benchmark.py so both
    paths find the same already-validated local install."""
    import pytesseract

    for candidate in _TESSERACT_CANDIDATES:
        if Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            break
    for pattern in _POPPLER_GLOB_CANDIDATES:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def ocr_page(pdf_path: Path, page_number: int) -> tuple[str, float]:
    """OCR a single 1-based page. Returns (text, mean_word_confidence 0-1).

    mean_word_confidence is Tesseract's own reported confidence; words with
    conf == -1 (no detection, per pytesseract) are excluded rather than
    counted as zero confidence.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise OCRUnavailableError(f"OCR dependency not installed: {exc}") from exc

    poppler_path = _configure_windows_binaries()
    try:
        images = convert_from_path(str(pdf_path), first_page=page_number, last_page=page_number,
                                    poppler_path=poppler_path)
    except Exception as exc:  # noqa: BLE001 - external tool, surface as OCRUnavailableError
        raise OCRUnavailableError(f"Page rasterization failed: {exc}") from exc
    if not images:
        raise OCRUnavailableError("Page rasterization produced no image")

    try:
        data = pytesseract.image_to_data(images[0], lang=OCR_LANGUAGES, config=f"--psm {OCR_PSM}",
                                          timeout=OCR_TIMEOUT_SECONDS, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(f"Tesseract binary not found: {exc}") from exc
    except RuntimeError as exc:
        raise OCRUnavailableError(f"Tesseract execution failed or timed out: {exc}") from exc

    words = [word for word in data["text"] if word.strip()]
    confidences = [int(conf) for conf, word in zip(data["conf"], data["text"])
                   if word.strip() and int(conf) >= 0]
    text = " ".join(words)
    mean_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
    return text, mean_confidence


def is_cover_page(page_number: int) -> bool:
    """See module docstring: positional proxy for "portada", validated only
    for page 1 of the one scanned sample measured so far."""
    return page_number == 1


def classify_ocr_result(page_number: int, mean_confidence: float) -> tuple[bool, ContentWarning]:
    """Apply DEC-04 routing to one OCR'd page. Returns (needs_review, warning)."""
    if is_cover_page(page_number):
        return True, ContentWarning(
            level="warning", code="OCR_COVER_PAGE_UNVALIDATED", page_number=page_number,
            confidence=mean_confidence,
            message=("Cover-page OCR has no validated accuracy threshold for this project "
                     "(CER stayed at 3.723%, above the 2% gate, across 14 preprocessing "
                     "experiments; DEC-04). Always needs review regardless of confidence."),
        )
    if mean_confidence < MIN_WORD_CONFIDENCE:
        return True, ContentWarning(
            level="warning", code="OCR_LOW_CONFIDENCE", page_number=page_number,
            confidence=mean_confidence,
            message=f"OCR mean word confidence {mean_confidence:.0%} is below the {MIN_WORD_CONFIDENCE:.0%} floor.",
        )
    return False, ContentWarning(
        level="info", code="OCR_APPLIED", page_number=page_number, confidence=mean_confidence,
        message=f"OCR applied with mean word confidence {mean_confidence:.0%}.",
    )
