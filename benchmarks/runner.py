#!/usr/bin/env python3
"""P02 - Full F0 benchmark run: tables + OCR, checked against Gate F0 thresholds.

Usage:
    python benchmarks/runner.py
    make benchmark

Thresholds below come from docs/ALCANCE.md ("Criterios de Éxito por Formato").
This script does not auto-decide Go/No-Go (Gate F0 is a separate decision) - it only
reports whether the measured metrics clear each threshold, so the Gate F0
discussion starts from evidence instead of opinion.
"""
from __future__ import annotations

import ocr_benchmark
import tables_benchmark
from common import MANIFEST_PATH

GATE_THRESHOLDS = {
    "tables_f1_digital_simple": 0.95,
    "tables_f1_digital_complex": 0.95,
    "ocr_cer_scanned_clean": 0.02,
}


def _avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def check_gate(table_results, ocr_results) -> None:
    print("\n=== Gate F0 - Evaluación contra umbrales (docs/ALCANCE.md) ===")

    simple_f1 = _avg(
        [
            r.metrics["f1"]
            for r in table_results
            if r.category == "digital_simple_table" and "f1" in r.metrics and r.error is None
        ]
    )
    complex_f1 = _avg(
        [
            r.metrics["f1"]
            for r in table_results
            if r.category == "digital_complex_table" and "f1" in r.metrics and r.error is None
        ]
    )
    scanned_clean_cer = _avg(
        [
            r.metrics["cer"]
            for r in ocr_results
            if r.category == "scanned_clean" and r.metrics.get("cer") is not None and r.error is None
        ]
    )

    def report(label: str, value: float | None, threshold: float, higher_is_better: bool) -> None:
        if value is None:
            print(f"  [SIN DATOS] {label}: no hay mediciones todavía (falta corpus/ground truth)")
            return
        passed = (value >= threshold) if higher_is_better else (value <= threshold)
        status = "PASA" if passed else "NO PASA"
        comparator = ">=" if higher_is_better else "<="
        print(f"  [{status}] {label}: {value:.3f} ({comparator} {threshold})")

    report("F1 tablas digital_simple_table", simple_f1, GATE_THRESHOLDS["tables_f1_digital_simple"], True)
    report("F1 tablas digital_complex_table", complex_f1, GATE_THRESHOLDS["tables_f1_digital_complex"], True)
    report("CER OCR scanned_clean", scanned_clean_cer, GATE_THRESHOLDS["ocr_cer_scanned_clean"], False)

    print(
        "\nNota: esto es evidencia de entrada para Gate F0 (decisión Go/No-Go), "
        "no un veredicto automático. Actualiza docs/AVANCE.md con el resultado."
    )


def main() -> None:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: no se encontró el manifest en {MANIFEST_PATH}")
        print("Ver benchmarks/README.md para preparar el corpus (P01) antes de correr P02.")
        raise SystemExit(1)

    table_results, table_skipped = tables_benchmark.run()
    ocr_results, ocr_skipped = ocr_benchmark.run()

    from common import print_summary, write_results

    write_results("tables_benchmark", table_results, table_skipped)
    write_results("ocr_benchmark", ocr_results, ocr_skipped)

    print_summary("P02 - Table Extraction Benchmark", table_results, table_skipped, metric_key="f1")
    print_summary("P02 - OCR Benchmark", ocr_results, ocr_skipped, metric_key="cer")
    check_gate(table_results, ocr_results)


if __name__ == "__main__":
    main()
