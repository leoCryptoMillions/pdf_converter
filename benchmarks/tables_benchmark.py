#!/usr/bin/env python3
"""P02 - Compare table-extraction engines (pdfplumber vs Camelot vs Docling).

Usage:
    python benchmarks/tables_benchmark.py
    make benchmark-tables

Writes benchmarks/results/tables_benchmark.json and prints a summary with
precision/recall/F1 per engine, measured against ground_truth/<file_id>.json
for the table-bearing categories (digital_simple_table, digital_complex_table).

Gate F0 threshold (docs/ALCANCE.md): F1 >= 0.95 for digital_simple_table.
"""
from __future__ import annotations

import time

from common import (
    EngineResult,
    load_ground_truth,
    load_manifest,
    print_summary,
    table_f1,
    usable_rows,
    write_results,
)

TABLE_CATEGORIES = {"digital_simple_table", "digital_complex_table"}


def extract_with_pdfplumber(pdf_path) -> list[list[list[str]]]:
    import pdfplumber

    tables: list[list[list[str]]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    return tables


def extract_with_camelot(pdf_path) -> list[list[list[str]]]:
    import camelot

    result = camelot.read_pdf(str(pdf_path), pages="all")
    return [t.df.values.tolist() for t in result]


def extract_with_docling(pdf_path) -> list[list[list[str]]]:
    # Docling's public API has changed across versions; this adapter is the
    # single place to update when pinning docling==1.1.0's actual interface.
    # Kept isolated so P02 can run partial results (pdfplumber/Camelot) even
    # if this adapter needs adjustment once run against real documents.
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    tables: list[list[list[str]]] = []
    for table in getattr(result.document, "tables", []):
        rows = table.export_to_dataframe().values.tolist()
        tables.append(rows)
    return tables


ENGINES = {
    "pdfplumber": extract_with_pdfplumber,
    "camelot": extract_with_camelot,
    "docling": extract_with_docling,
}


def run() -> tuple[list[EngineResult], list[str]]:
    manifest = load_manifest()
    rows, skipped = usable_rows(manifest, categories=TABLE_CATEGORIES)
    results: list[EngineResult] = []

    if not rows:
        return results, skipped

    for row in rows:
        ground_truth = load_ground_truth(row.file_id)
        expected_tables = []
        if ground_truth:
            for page in ground_truth.get("pages", []):
                expected_tables.extend(page.get("tables", []))

        for engine_name, extract_fn in ENGINES.items():
            start = time.monotonic()
            try:
                actual_tables = extract_fn(row.pdf_path)
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
            metrics = table_f1(expected_tables, actual_tables) if expected_tables else {}
            if not expected_tables:
                metrics["note"] = "no ground truth - timing only, no F1 computed"
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
    write_results("tables_benchmark", results, skipped)
    print_summary("P02 - Table Extraction Benchmark", results, skipped, metric_key="f1")


if __name__ == "__main__":
    main()
