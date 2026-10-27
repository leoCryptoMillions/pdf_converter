"""Process isolation, hard timeout, memory cap and TTL cleanup for the F0
local-review MVP (apps/local_review_ui.py).

Why this exists: extract_digital (packages/converters/digital.py) has no
wall-clock timeout and no memory ceiling anywhere in its parse path, and the
MVP's /convert handler used to call it synchronously inline inside an async
handler, blocking the single uvicorn worker. Now deployed on a reachable
host (see docs/adr/0006-mvp-railway-hardening.md), a pathological PDF must
not be able to hang or OOM the whole process. Each conversion runs in a
fresh subprocess (not a pool, so a hung/bombed child never poisons a
reusable worker and Windows' spawn semantics - this module's target must be
importable at module scope, not a closure) with a hard kill on timeout and a
best-effort memory limit. Only a small, flat, picklable summary crosses the
process boundary - never the full DocumentIR, which can carry embedded
image bytes.
"""
from __future__ import annotations

import asyncio
import multiprocessing as mp
import os
import shutil
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

CONVERT_TIMEOUT_SECONDS = float(os.environ.get("CONVERT_TIMEOUT_SECONDS", "90"))
CONVERT_GRACE_SECONDS = float(os.environ.get("CONVERT_GRACE_SECONDS", "5"))
CONVERT_MEMORY_LIMIT_MB = int(os.environ.get("CONVERT_MEMORY_LIMIT_MB", "768"))
RETENTION_HOURS = float(os.environ.get("RETENTION_HOURS", "24"))
CLEANUP_INTERVAL_SECONDS = float(os.environ.get("CLEANUP_INTERVAL_SECONDS", "3600"))


@dataclass
class ConversionSummary:
    """Flat, picklable result of an isolated conversion. Never carries the
    DocumentIR itself (see module docstring)."""
    ok: bool
    page_count: int = 0
    pages_processed: int = 0
    table_count: int = 0
    text_preview: str = ""
    text_truncated: bool = False
    warnings: list[dict] = field(default_factory=list)
    artifact_names: list[str] = field(default_factory=list)
    error_kind: str = ""  # "validation" | "memory" | "timeout" | "export_value_error" | "crash"
    error_message: str = ""


def _apply_memory_limit(limit_mb: int) -> None:
    """Best-effort RLIMIT_AS cap. No-op on platforms without `resource`
    (Windows) or that reject RLIMIT_AS (some macOS setups) - the timeout and,
    on Railway, the container's own cgroup memory limit are the backstops."""
    if limit_mb <= 0:
        return
    try:
        import resource
    except ImportError:
        return
    limit_bytes = limit_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except (ValueError, OSError):
        pass


def _child_main(conn, job_dir: str, source_path: str, page_numbers: list[int] | None,
                 ocr: bool, selected_formats: frozenset[str], docx_warnings: bool,
                 memory_limit_mb: int) -> None:
    """Runs in the isolated subprocess. Writes artifacts directly into
    job_dir; sends only a ConversionSummary back over the pipe."""
    _apply_memory_limit(memory_limit_mb)
    try:
        from packages.converters.digital import PDFValidationError, extract_digital

        document = extract_digital(Path(source_path), page_numbers=page_numbers, ocr=ocr,
                                    preserve_layout="docx" in selected_formats)

        job_dir_path = Path(job_dir)
        written: list[str] = []
        if "xlsx" in selected_formats:
            from packages.exporters.xlsx import export_xlsx
            (job_dir_path / "result.xlsx").write_bytes(export_xlsx(document))
            written.append("result.xlsx")
        if "docx" in selected_formats:
            from packages.exporters.docx import export_docx
            (job_dir_path / "result.docx").write_bytes(
                export_docx(document, include_warnings=docx_warnings))
            written.append("result.docx")
        if "txt" in selected_formats:
            (job_dir_path / "result.txt").write_bytes(document.get_all_text().encode("utf-8"))
            written.append("result.txt")
        (job_dir_path / "document.ir.json").write_bytes(
            document.model_dump_json(indent=2).encode("utf-8"))
        written.append("document.ir.json")

        text = document.get_all_text()
        warnings = document.warnings + [w for p in document.pages for w in p.warnings]
        conn.send(ConversionSummary(
            ok=True,
            page_count=document.page_count,
            pages_processed=len(document.pages),
            table_count=len(document.get_all_tables()),
            text_preview=text[:6000],
            text_truncated=len(text) > 6000,
            warnings=[{"code": w.code, "message": w.message, "page_number": w.page_number,
                       "level": w.level} for w in warnings],
            artifact_names=written,
        ))
    except PDFValidationError as exc:
        conn.send(ConversionSummary(ok=False, error_kind="validation", error_message=str(exc)))
    except MemoryError:
        conn.send(ConversionSummary(ok=False, error_kind="memory",
                                     error_message="memory limit exceeded"))
    except ValueError as exc:
        conn.send(ConversionSummary(ok=False, error_kind="export_value_error",
                                     error_message=str(exc)))
    except Exception:
        conn.send(ConversionSummary(ok=False, error_kind="crash",
                                     error_message=traceback.format_exc(limit=5)))
    finally:
        conn.close()


def run_isolated(job_dir: Path, source_path: Path, *, page_numbers: list[int] | None,
                  ocr: bool, selected_formats: frozenset[str], docx_warnings: bool,
                  child_target=_child_main) -> ConversionSummary:
    """Blocking: spawn an isolated child, wait up to CONVERT_TIMEOUT_SECONDS,
    hard-kill on overrun. Call via loop.run_in_executor from async code so the
    event loop isn't blocked while this waits on the child."""
    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(
        target=child_target,
        args=(child_conn, str(job_dir), str(source_path), page_numbers, ocr,
              selected_formats, docx_warnings, CONVERT_MEMORY_LIMIT_MB),
        daemon=True,
    )
    proc.start()
    child_conn.close()
    proc.join(CONVERT_TIMEOUT_SECONDS)
    if proc.is_alive():
        proc.terminate()
        proc.join(CONVERT_GRACE_SECONDS)
        if proc.is_alive():
            proc.kill()
            proc.join()
        return ConversionSummary(ok=False, error_kind="timeout",
                                  error_message=f"conversion exceeded {CONVERT_TIMEOUT_SECONDS:.0f}s")
    if parent_conn.poll():
        return parent_conn.recv()
    return ConversionSummary(ok=False, error_kind="crash",
                              error_message=f"child exited with code {proc.exitcode}")


def prune_old_jobs(output_root: Path, retention_hours: float, *, now: float | None = None) -> list[str]:
    """Pure, synchronous: delete job directories whose newest file is older
    than retention_hours. Returns the removed job ids."""
    now = time.time() if now is None else now
    cutoff = now - retention_hours * 3600
    removed = []
    if not output_root.is_dir():
        return removed
    for job_dir in output_root.iterdir():
        if not job_dir.is_dir():
            continue
        try:
            newest = max((p.stat().st_mtime for p in job_dir.rglob("*") if p.is_file()),
                         default=job_dir.stat().st_mtime)
        except FileNotFoundError:
            continue
        if newest < cutoff:
            shutil.rmtree(job_dir, ignore_errors=True)
            removed.append(job_dir.name)
    return removed


async def cleanup_loop(output_root: Path, retention_hours: float, interval_seconds: float) -> None:
    """Background sweep started at FastAPI startup. Bounds disk usage on a
    long-lived container regardless of traffic (unlike pruning only on
    request, which never runs if nobody uploads anything)."""
    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(interval_seconds)
        await loop.run_in_executor(None, prune_old_jobs, output_root, retention_hours)
