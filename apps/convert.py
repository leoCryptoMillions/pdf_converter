"""Local F0 CLI. Run: python -m apps.convert input.pdf --output .generated/demo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from packages.converters.digital import PDFValidationError, extract_digital


def main() -> None:
    parser = argparse.ArgumentParser(description="Local PDF conversion prototype (F0)")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="New directory for artifacts")
    parser.add_argument("--formats", nargs="+", choices=["xlsx", "docx", "txt"], default=["xlsx"])
    parser.add_argument("--types", type=Path, help="JSON table_id -> zero-based column -> numeric type")
    parser.add_argument("--pages", nargs="+", type=int, help="1-based source pages; defaults to all pages")
    args = parser.parse_args()
    try:
        document = extract_digital(args.source, page_numbers=args.pages)
        types = {}
        if args.types:
            types = {key: {int(col): value for col, value in columns.items()}
                     for key, columns in json.loads(args.types.read_text(encoding="utf-8")).items()}
        artifacts = {"document.ir.json": document.model_dump_json(indent=2).encode("utf-8")}
        for fmt in set(args.formats):
            if fmt == "xlsx":
                from packages.exporters.xlsx import export_xlsx
                data = export_xlsx(document, numeric_columns=types)
            elif fmt == "docx":
                from packages.exporters.docx import export_docx
                data = export_docx(document)
            else:
                data = document.get_all_text().encode("utf-8")
            artifacts[f"result.{fmt}"] = data
        # Never overwrite an earlier conversion; assemble before publishing.
        args.output.mkdir(parents=True, exist_ok=False)
        for name, data in artifacts.items():
            (args.output / name).write_bytes(data)
        summary = {"status": "needs_review", "pages": len(document.pages), "source_pages": document.page_count,
                   "tables": len(document.get_all_tables()), "artifacts": list(artifacts)}
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary))
    except (PDFValidationError, ValueError, OSError, ImportError) as exc:
        parser.exit(1, f"Conversion failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
