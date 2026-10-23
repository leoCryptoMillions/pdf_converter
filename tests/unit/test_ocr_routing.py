"""DEC-04 OCR routing (docs/AVANCE.md, 2026-10-20): cover pages ("portada")
always need review; continuous-text pages route on Tesseract's own
confidence. See packages/converters/ocr.py for the full rationale.
"""
from pathlib import Path

import pytest

from packages.converters.digital import extract_digital
from packages.converters.ocr import classify_ocr_result, is_cover_page

CORPUS_SAMPLE = Path("benchmarks/corpus/files/manualcargadorBYD.pdf")
try:
    import pytesseract
    from pdf2image import convert_from_path  # noqa: F401

    from packages.converters.ocr import _configure_windows_binaries

    _configure_windows_binaries()
    pytesseract.get_tesseract_version()
    OCR_AVAILABLE = True
except Exception:  # noqa: BLE001 - any missing/broken OCR dependency just skips below
    OCR_AVAILABLE = False


def test_is_cover_page_is_positional_not_visual():
    assert is_cover_page(1) is True
    assert is_cover_page(2) is False
    assert is_cover_page(3) is False


def test_cover_page_always_needs_review_regardless_of_confidence():
    needs_review, warning = classify_ocr_result(1, mean_confidence=0.99)
    assert needs_review is True
    assert warning.code == "OCR_COVER_PAGE_UNVALIDATED"


def test_continuous_text_page_routes_on_confidence_floor():
    low_review, low_warning = classify_ocr_result(2, mean_confidence=0.84)
    assert low_review is True
    assert low_warning.code == "OCR_LOW_CONFIDENCE"

    high_review, high_warning = classify_ocr_result(2, mean_confidence=0.85)
    assert high_review is False
    assert high_warning.code == "OCR_APPLIED"


def test_ocr_disabled_by_default_keeps_existing_behavior():
    document = extract_digital(CORPUS_SAMPLE, page_numbers=[1])
    page = document.pages[0]
    assert page.extracted_text == ""
    assert any(w.code == "OCR_REQUIRED" for w in page.warnings)
    assert document.ocr_enabled is False


@pytest.mark.skipif(not OCR_AVAILABLE, reason="Tesseract/poppler not available in this environment")
@pytest.mark.skipif(not CORPUS_SAMPLE.exists(), reason="corpus sample not present")
def test_real_ocr_routes_cover_and_continuous_pages_differently():
    document = extract_digital(CORPUS_SAMPLE, page_numbers=[1, 3], ocr=True)
    assert document.ocr_enabled is True
    cover, continuous = document.pages

    assert cover.page_number == 1
    assert cover.extracted_text.strip()
    assert cover.metadata["ocr_needs_review"] is True
    assert any(w.code == "OCR_COVER_PAGE_UNVALIDATED" for w in cover.warnings)

    assert continuous.page_number == 3
    assert continuous.extracted_text.strip()
    assert any(w.code in {"OCR_APPLIED", "OCR_LOW_CONFIDENCE"} for w in continuous.warnings)
    # Validated in docs/PROTOTIPO_F0.md: continuous text OCRs cleanly (CER 0.968%).
    assert continuous.metadata["ocr_mean_confidence"] >= 0.85
    assert continuous.metadata["ocr_needs_review"] is False
