"""Shared helpers for F0 benchmark scripts (tables_benchmark.py, ocr_benchmark.py, runner.py).

Reads the corpus manifest and ground truth, and computes the metrics used
by the Gate F0 criteria defined in docs/ALCANCE.md.
"""
from __future__ import annotations

import csv
import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BENCHMARKS_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BENCHMARKS_DIR / "corpus" / "files"
GROUND_TRUTH_DIR = BENCHMARKS_DIR / "ground_truth"
MANIFEST_PATH = BENCHMARKS_DIR / "corpus_manifest.csv"
RESULTS_DIR = BENCHMARKS_DIR / "results"


@dataclass
class ManifestRow:
    file_id: str
    filename: str
    category: str
    page_count: int
    source: str
    authorized: bool
    has_ground_truth: bool
    notes: str = ""

    @property
    def pdf_path(self) -> Path:
        return CORPUS_DIR / self.filename


@dataclass
class EngineResult:
    engine: str
    file_id: str
    category: str
    duration_s: float
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    skipped_reason: str | None = None


def load_manifest(path: Path = MANIFEST_PATH) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            rows.append(
                ManifestRow(
                    file_id=raw["file_id"],
                    filename=raw["filename"],
                    category=raw["category"],
                    page_count=int(raw["page_count"] or 0),
                    source=raw["source"],
                    authorized=raw["authorized"].strip().lower() == "yes",
                    has_ground_truth=raw["has_ground_truth"].strip().lower() == "yes",
                    notes=raw.get("notes", ""),
                )
            )
    return rows


def usable_rows(rows: list[ManifestRow], categories: set[str] | None = None) -> tuple[list[ManifestRow], list[str]]:
    """Filter manifest rows to ones that can actually be benchmarked.

    Returns (usable, skipped_messages). Never silently drops rows - every
    skip is reported so coverage gaps are visible (see benchmarks/README.md).
    """
    usable: list[ManifestRow] = []
    skipped: list[str] = []
    for row in rows:
        if categories is not None and row.category not in categories:
            continue
        if not row.authorized:
            skipped.append(f"{row.file_id}: skipped (authorized != yes)")
            continue
        if not row.pdf_path.exists():
            skipped.append(f"{row.file_id}: skipped (PDF not found at {row.pdf_path})")
            continue
        usable.append(row)
    return usable, skipped


def load_ground_truth(file_id: str) -> dict[str, Any] | None:
    path = GROUND_TRUTH_DIR / f"{file_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def character_error_rate(expected: str, actual: str) -> float:
    """CER = edit distance / len(expected), using difflib's opcode-based distance."""
    if not expected:
        return 0.0 if not actual else 1.0
    matcher = difflib.SequenceMatcher(a=expected, b=actual, autojunk=False)
    edits = sum(
        max(i2 - i1, j2 - j1)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    )
    return edits / len(expected)


def text_accuracy(expected: str, actual: str) -> float:
    """Normalized similarity ratio in [0, 1] - used as a proxy for 'content coverage'."""
    if not expected and not actual:
        return 1.0
    return difflib.SequenceMatcher(a=expected, b=actual, autojunk=False).ratio()


def _normalize_row(row: list[str]) -> tuple[str, ...]:
    return tuple((cell or "").strip() for cell in row)


def table_f1(expected_tables: list[dict], actual_tables: list[list[list[str]]]) -> dict[str, float]:
    """Row-level precision/recall/F1 between expected and extracted tables.

    Tables are matched positionally (table 0 vs table 0, ...); rows within a
    table are compared as exact-match sets after whitespace normalization.
    This is intentionally simple - tune per docs/ALCANCE.md needs once real
    corpus data exposes edge cases (merged cells, header-only mismatches).
    """
    expected_rows: set[tuple[str, ...]] = set()
    for t_idx, table in enumerate(expected_tables):
        for row in table.get("rows", []):
            expected_rows.add((t_idx, _normalize_row(row)))

    actual_rows: set[tuple[str, ...]] = set()
    for t_idx, table in enumerate(actual_tables):
        for row in table:
            actual_rows.add((t_idx, _normalize_row(row)))

    true_positives = len(expected_rows & actual_rows)
    precision = true_positives / len(actual_rows) if actual_rows else 0.0
    recall = true_positives / len(expected_rows) if expected_rows else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def write_results(name: str, results: list[EngineResult], skipped: list[str]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{name}.json"
    payload = {
        "skipped": skipped,
        "results": [
            {
                "engine": r.engine,
                "file_id": r.file_id,
                "category": r.category,
                "duration_s": r.duration_s,
                "metrics": r.metrics,
                "error": r.error,
                "skipped_reason": r.skipped_reason,
            }
            for r in results
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def print_summary(title: str, results: list[EngineResult], skipped: list[str], metric_key: str) -> None:
    print(f"\n=== {title} ===")
    if skipped:
        print(f"Skipped {len(skipped)} manifest row(s):")
        for msg in skipped:
            print(f"  - {msg}")
    if not results:
        print("No results produced (corpus not ready yet - see benchmarks/README.md).")
        return

    by_engine: dict[str, list[EngineResult]] = {}
    for r in results:
        by_engine.setdefault(r.engine, []).append(r)

    print(f"\n{'Engine':<15}{'N':<6}{'Errors':<8}{'Avg ' + metric_key:<15}{'Avg duration (s)':<18}")
    for engine, items in sorted(by_engine.items()):
        ok = [r for r in items if r.error is None]
        errors = len(items) - len(ok)
        avg_metric = sum(r.metrics.get(metric_key, 0.0) for r in ok) / len(ok) if ok else 0.0
        avg_duration = sum(r.duration_s for r in ok) / len(ok) if ok else 0.0
        print(f"{engine:<15}{len(items):<6}{errors:<8}{avg_metric:<15.3f}{avg_duration:<18.2f}")
