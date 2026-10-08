"""Development-only OCR experiment; fixed variants, no reference-based correction."""
import json
from pathlib import Path
import time

from benchmarks.common import character_error_rate, load_ground_truth, load_manifest
from benchmarks.validate_prototype import normalize, ocr_page_text

VARIANTS = [(3, 300, "none"), (11, 300, "none"), (3, 300, "autocontrast"),
            (11, 300, "autocontrast"), (3, 300, "threshold160"),
            (11, 300, "threshold160"), (3, 450, "none")]


def run() -> dict:
    row = next(r for r in load_manifest() if r.file_id == "scanned_002")
    reference = load_ground_truth(row.file_id)
    if not row.authorized or not reference:
        raise ValueError("Authorized source and reference required")
    output = Path(".generated/f0/ocr_experiments")
    output.mkdir(parents=True, exist_ok=True)
    report = {"scope": "development experiment on two previously inspected pages; not held-out evidence",
              "file_id": row.file_id, "results": []}
    for page in reference["pages"]:
        for psm, dpi, preprocess in VARIANTS:
            result = {"page": page["page_number"], "psm": psm, "dpi": dpi, "preprocess": preprocess}
            started = time.monotonic()
            try:
                text = ocr_page_text(row.pdf_path, page["page_number"], psm=psm, dpi=dpi, preprocess=preprocess)
                result["cer_whitespace_normalized"] = character_error_rate(normalize(page["text"]), normalize(text))
                result["cer_raw"] = character_error_rate(page["text"], text)
                name = f"p{page['page_number']}_psm{psm}_{dpi}_{preprocess}.txt"
                (output / name).write_text(text, encoding="utf-8")
            except Exception as exc:
                result["error"] = type(exc).__name__
            result["duration_s"] = time.monotonic() - started
            report["results"].append(result)
            (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
