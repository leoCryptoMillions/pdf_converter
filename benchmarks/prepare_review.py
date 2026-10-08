"""Create local annotation tasks and a hash-grouped development/evaluation split.

Run: python -m benchmarks.prepare_review
No engine output is used as ground truth; templates remain unverified drafts.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict

from benchmarks.common import BENCHMARKS_DIR, load_ground_truth, load_manifest, usable_rows


def main() -> None:
    rows, skipped = usable_rows(load_manifest())
    directory = BENCHMARKS_DIR / "review"
    directory.mkdir(exist_ok=True)
    grouped = defaultdict(list)
    records = []
    for row in rows:
        digest = hashlib.sha256(row.pdf_path.read_bytes()).hexdigest()
        # Identical PDFs must never be split across development and evaluation.
        split = "evaluation" if int(digest[:8], 16) % 5 == 0 else "development"
        reference = load_ground_truth(row.file_id)
        record = {"file_id": row.file_id, "category": row.category, "page_count": row.page_count,
                  "sha256": digest, "split": split,
                  "reference_scope": reference.get("scope", "legacy_tables") if reference else "missing"}
        records.append(record)
        if not row.category.startswith("adversarial_"):
            grouped[row.category].append((row, digest))
    tasks = []
    seen = set()
    for category, candidates in sorted(grouped.items()):
        selected = 0
        for row, digest in sorted(candidates, key=lambda pair: (pair[0].page_count, pair[0].file_id)):
            reference = load_ground_truth(row.file_id)
            if digest in seen or (reference and reference.get("scope") in {"full_text", "tables_only"}) or (reference and reference.get("scope") is None):
                continue
            seen.add(digest)
            reviewed = {p["page_number"] for p in reference["pages"]} if reference else set()
            remaining = [number for number in range(1, row.page_count + 1) if number not in reviewed]
            pages_to_review = remaining[:2] if reference and remaining else [1]
            tasks.append({"file_id": row.file_id, "category": category,
                          "pages_to_review": pages_to_review, "review_status": "draft",
                          "mode": "extend_reference" if reference else "new_reference",
                          "source_sha256": digest,
                          "instructions": "Transcribe from a rendered page; review critical cells independently. Do not accept extracted text as truth."})
            selected += 1
            if selected == 2:
                break
    with (directory / "corpus_split.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]) if records else ["file_id"])
        writer.writeheader()
        writer.writerows(records)
    (directory / "annotation_tasks.json").write_text(
        json.dumps({"tasks": tasks, "skipped": skipped}, indent=2), encoding="utf-8")
    print(json.dumps({"corpus": len(records), "annotation_tasks": len(tasks),
                      "split": "hash-grouped proposal; verify balance before freezing evaluation"}))


if __name__ == "__main__":
    main()
