#!/usr/bin/env python3
"""P02 - OCR benchmark (Tesseract), with and without OCRmyPDF preprocessing.

Usage:
    python benchmarks/ocr_benchmark.py
    make benchmark-ocr

Writes benchmarks/results/ocr_benchmark.json and prints a summary with
Character Error Rate (CER) per engine variant, measured against
ground_truth/<file_id>.json for the scanned categories.

Gate F0 threshold (docs/ALCANCE.md): CER <= 2% on scanned_clean.
"""
from __future__ import annotations

import glob
import os
import tempfile
import time
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks.common import (
    BENCHMARKS_DIR,
    EngineResult,
    character_error_rate,
    load_ground_truth,
    load_manifest,
    print_summary,
    usable_rows,
    write_results,
)

OCR_CATEGORIES = {"scanned_clean", "scanned_difficult", "mixed"}
OCR_LANGUAGES = "spa+eng"

# Windows has no system-wide "just works" install for Tesseract/Poppler - both
# are native binaries, not pip packages. Auto-detect common install locations
# instead of requiring every shell session to manually set PATH, which is easy
# to forget and then silently falls back to "dependency not installed".
_LOCAL_TESSDATA = BENCHMARKS_DIR / ".tessdata"
if _LOCAL_TESSDATA.is_dir():
    os.environ.setdefault("TESSDATA_PREFIX", str(_LOCAL_TESSDATA))

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
_POPPLER_GLOB_CANDIDATES = [
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Packages/*Poppler*/poppler-*/Library/bin"),
]


def _configure_windows_binaries() -> str | None:
    """Return a poppler bin dir to pass to pdf2image, and point pytesseract at
    tesseract.exe, if found in a known winget install location."""
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


_POPPLER_PATH = _configure_windows_binaries()


def _page_images(pdf_path: Path):
    from pdf2image import convert_from_path

    return convert_from_path(str(pdf_path), poppler_path=_POPPLER_PATH)


def ocr_tesseract(pdf_path: Path) -> str:
    import pytesseract

    pages = _page_images(pdf_path)
    return "\n".join(pytesseract.image_to_string(page, lang=OCR_LANGUAGES) for page in pages)


def ocr_tesseract_with_ocrmypdf(pdf_path: Path) -> str:
    import ocrmypdf
    import pytesseract

    with tempfile.TemporaryDirectory() as tmp:
        preprocessed = Path(tmp) / "preprocessed.pdf"
        ocrmypdf.ocr(
            str(pdf_path),
            str(preprocessed),
            language=OCR_LANGUAGES.replace("+", "+"),
            deskew=True,
            rotate_pages=True,
            force_ocr=True,
            progress_bar=False,
        )
        pages = _page_images(preprocessed)
        return "\n".join(pytesseract.image_to_string(page, lang=OCR_LANGUAGES) for page in pages)


ENGINES = {
    "tesseract": ocr_tesseract,
    "tesseract+ocrmypdf": ocr_tesseract_with_ocrmypdf,
}


def run() -> tuple[list[EngineResult], list[str]]:
    manifest = load_manifest()
    rows, skipped = usable_rows(manifest, categories=OCR_CATEGORIES)
    results: list[EngineResult] = []

    if not rows:
        return results, skipped

    for row in rows:
        ground_truth = load_ground_truth(row.file_id)
        expected_text = ""
        if ground_truth and ground_truth.get("scope") not in {"selected_pages_text", "text_region"}:
            expected_text = "\n".join(p.get("text", "") for p in ground_truth.get("pages", []))

        for engine_name, ocr_fn in ENGINES.items():
            start = time.monotonic()
            try:
                actual_text = ocr_fn(row.pdf_path)
            except ImportError as exc:
                results.append(
                    EngineResult(
                        engine=engine_name,
                        file_id=row.file_id,
                        category=row.category,
                        duration_s=0.0,
                        skipped_reason=f"dependency not installed: {exc}",
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 - benchmark must keep going per engine
                results.append(
                    EngineResult(
                        engine=engine_name,
                        file_id=row.file_id,
                        category=row.category,
                        duration_s=time.monotonic() - start,
                        error=str(exc),
                    )
                )
                continue

            duration = time.monotonic() - start
            if expected_text:
                cer = character_error_rate(expected_text, actual_text)
                metrics = {"cer": cer}
            else:
                metrics = {"cer": None, "note": "no ground truth - timing only, no CER computed"}
                if ground_truth and ground_truth.get("scope") in {"selected_pages_text", "text_region"}:
                    metrics["note"] = "partial-document reference; use validate_prototype for scoped page/region CER"
            results.append(
                EngineResult(
                    engine=engine_name,
                    file_id=row.file_id,
                    category=row.category,
                    duration_s=duration,
                    metrics=metrics,
                )
            )

    return results, skipped


def main() -> None:
    results, skipped = run()
    write_results("ocr_benchmark", results, skipped)
    print_summary("P02 - OCR Benchmark", results, skipped, metric_key="cer")


if __name__ == "__main__":
    main()
