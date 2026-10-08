"""Shared helpers for F0 benchmark scripts (tables_benchmark.py, ocr_benchmark.py, runner.py).

Reads the corpus manifest and ground truth, and computes the metrics used
by the Gate F0 criteria defined in docs/ALCANCE.md.
"""
from __future__ import annotations

import csv
from collections import Counter
import difflib
import json
import hashlib
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
    if Path(file_id).name != file_id or file_id in {".", ".."}:
        raise ValueError("Invalid reference ID")
    for directory in (GROUND_TRUTH_DIR / "local", GROUND_TRUTH_DIR):
        path = directory / f"{file_id}.json"
        if path.exists():
            reference = json.loads(path.read_text(encoding="utf-8"))
            if reference.get("review_status", "verified") != "verified":
                return None
            if "source_sha256" in reference:
                row = next((r for r in load_manifest() if r.file_id == file_id), None)
                if row is None or not row.authorized or not row.pdf_path.is_file():
                    raise ValueError(f"Reference source unavailable: {file_id}")
                if hashlib.sha256(row.pdf_path.read_bytes()).hexdigest() != reference["source_sha256"]:
                    raise ValueError(f"Reference hash mismatch: {file_id}")
            return reference
    return None


def character_error_rate(expected: str, actual: str) -> float:
    """CER = exact Levenshtein distance / reference length (can exceed 1)."""
    if not expected:
        return 0.0 if not actual else 1.0
    denominator = len(expected)
    if expected == actual:
        return 0.0
    # Reduce memory to O(min(n, m)); exact dynamic programming, no approximation.
    if len(expected) > len(actual):
        expected, actual = actual, expected
    previous = list(range(len(expected) + 1))
    for i, char in enumerate(actual, 1):
        current = [i]
        for j, ref in enumerate(expected, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (char != ref)))
        previous = current
    return previous[-1] / denominator


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
    table are compared as exact-match multisets after trimming cell edges.
    Duplicate row counts are preserved. This does not measure cell geometry
    or row ordering, so it must not be reported as structure/detection F1.
    This is intentionally simple - tune per docs/ALCANCE.md needs once real
    corpus data exposes edge cases (merged cells, header-only mismatches).
    """
    expected_rows = Counter()
    for t_idx, table in enumerate(expected_tables):
        for row in table.get("rows", []):
            expected_rows[(t_idx, _normalize_row(row))] += 1

    actual_rows = Counter()
    for t_idx, table in enumerate(actual_tables):
        for row in table:
            actual_rows[(t_idx, _normalize_row(row))] += 1

    true_positives = sum((expected_rows & actual_rows).values())
    precision = true_positives / sum(actual_rows.values()) if actual_rows else 0.0
    recall = true_positives / sum(expected_rows.values()) if expected_rows else 0.0
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

    # Three mutually exclusive states per result - conflating them (e.g. counting
    # a "dependency not installed" skip as a successful 0-duration run) hides real
    # coverage gaps, which is exactly what this benchmark must never do silently.
    print(
        f"\n{'Engine':<22}{'N':<5}{'Ran':<6}{'Errors':<8}{'DepMissing':<12}"
        f"{'Scored':<8}{'Avg ' + metric_key:<12}{'Avg dur(s)':<12}"
    )
    for engine, items in sorted(by_engine.items()):
        dep_missing = [r for r in items if r.skipped_reason is not None]
        errored = [r for r in items if r.error is not None]
        ran = [r for r in items if r.error is None and r.skipped_reason is None]
        scored = [r for r in ran if r.metrics.get(metric_key) is not None]
        avg_metric_str = f"{sum(r.metrics[metric_key] for r in scored) / len(scored):.3f}" if scored else "n/a"
        avg_duration = sum(r.duration_s for r in ran) / len(ran) if ran else 0.0
        print(
            f"{engine:<22}{len(items):<5}{len(ran):<6}{len(errored):<8}{len(dep_missing):<12}"
            f"{len(scored):<8}{avg_metric_str:<12}{avg_duration:<12.2f}"
        )
        if dep_missing:
            print(f"    omitido (dependencia faltante): {dep_missing[0].skipped_reason}")
        if errored:
            print(f"    ejemplo de error: {errored[0].error}")
