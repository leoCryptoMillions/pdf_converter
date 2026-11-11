"""Supervised conversion with bounded IPC, process limits and explicit cleanup."""
from __future__ import annotations

import asyncio
from concurrent.futures import Future
from dataclasses import asdict, dataclass, field
import json
import logging
import multiprocessing as mp
import os
from pathlib import Path
import pickle
import signal
import threading
import time

from apps.job_store import FileLease, read_metadata, remove_job, write_artifact
from apps.memory_limits import limit_current_process
from apps.runtime_config import settings

logger = logging.getLogger("pdf_converter.conversion")
CONVERT_TIMEOUT_SECONDS = settings.timeout
CONVERT_GRACE_SECONDS = settings.grace
CONVERT_MEMORY_LIMIT_MB = settings.memory_mb
RETENTION_HOURS = settings.retention_hours
CLEANUP_INTERVAL_SECONDS = settings.cleanup_interval
MAX_IPC_BYTES = 1024 * 1024
MAX_UI_WARNINGS = 200


@dataclass
class ConversionSummary:
    ok: bool
    page_count: int = 0
    pages_processed: int = 0
    table_count: int = 0
    text_preview: str = ""
    text_truncated: bool = False
    warnings: list[dict] = field(default_factory=list)
    artifact_names: list[str] = field(default_factory=list)
    error_kind: str = ""
    error_message: str = ""
    warning_count: int = 0
    memory_backend: str = ""
    details_in_file: bool = False


def _apply_memory_limit(limit_mb: int) -> str:
    return limit_current_process(limit_mb)


def _child_main(conn, job_dir: str, source_path: str, page_numbers: list[int] | None,
                ocr: bool, selected_formats: frozenset[str], docx_warnings: bool,
                memory_limit_mb: int) -> None:
    validation_errors = ()
    try:
        if os.name != "nt":
            os.setsid()  # Supervisor can also stop optional OCR descendants.
        try:
            memory_backend = _apply_memory_limit(memory_limit_mb)
        except (OSError, ImportError, ValueError):
            conn.send(ConversionSummary(ok=False, error_kind="isolation"))
            return
        from packages.converters.digital import PDFValidationError, extract_digital
        from packages.document_ir.warnings import collect_warnings
        validation_errors = (PDFValidationError,)
        document = extract_digital(Path(source_path), page_numbers=page_numbers, ocr=ocr,
                                  preserve_layout=bool({"docx", "xlsx"} & selected_formats))
        directory = Path(job_dir)
        staging = directory / ".staging"
        written = []
        if "xlsx" in selected_formats:
            from packages.exporters.xlsx import export_xlsx
            write_artifact(directory, staging, "result.xlsx", export_xlsx(document))
            written.append("result.xlsx")
        if "docx" in selected_formats:
            from packages.exporters.docx import export_docx
            write_artifact(directory, staging, "result.docx",
                           export_docx(document, include_warnings=docx_warnings))
            written.append("result.docx")
        text = document.get_all_text()
        if "txt" in selected_formats:
            write_artifact(directory, staging, "result.txt", text.encode("utf-8"))
            written.append("result.txt")
        warnings = [issue.model_dump(mode="json", exclude_none=True) for issue in collect_warnings(document)]
        write_artifact(directory, staging, "warnings.json", json.dumps(warnings, ensure_ascii=False).encode("utf-8"))
        write_artifact(directory, staging, "document.ir.json", document.model_dump_json(indent=2).encode("utf-8"))
        written.extend(["warnings.json", "document.ir.json"])
        # Complete details stay on disk; fixed-budget UI data never carries images.
        preview_warnings = [dict(issue, message=issue["message"][:2000] + ("…" if len(issue["message"]) > 2000 else ""), code=issue["code"][:128])
                            for issue in warnings[:MAX_UI_WARNINGS]]
        summary = ConversionSummary(ok=True, page_count=document.page_count,
            pages_processed=len(document.pages), table_count=len(document.get_all_tables()),
            text_preview=text[:6000], text_truncated=len(text) > 6000,
            warnings=preview_warnings, warning_count=len(warnings), artifact_names=written,
            memory_backend=memory_backend)
        payload = json.dumps(asdict(summary), ensure_ascii=False).encode("utf-8")
        while len(payload) > MAX_IPC_BYTES and summary.warnings:
            summary.warnings = summary.warnings[:len(summary.warnings) // 2]
            payload = json.dumps(asdict(summary), ensure_ascii=False).encode("utf-8")
        if len(payload) > MAX_IPC_BYTES:
            raise ValueError("Summary exceeds budget")
        write_artifact(directory, directory, "conversion-summary.json", payload)
        conn.send(ConversionSummary(ok=True, details_in_file=True))
    except validation_errors as exc:
        conn.send(ConversionSummary(ok=False, error_kind="validation", error_message=str(exc)))
    except MemoryError:
        conn.send(ConversionSummary(ok=False, error_kind="memory"))
    except ValueError:
        conn.send(ConversionSummary(ok=False, error_kind="export_value_error"))
    except OSError:
        conn.send(ConversionSummary(ok=False, error_kind="storage"))
    except Exception:
        # Exception messages and tracebacks may contain extracted text or paths.
        conn.send(ConversionSummary(ok=False, error_kind="crash"))
    finally:
        conn.close()


def _stop_process(proc) -> None:
    if not proc.is_alive():
        return
    if os.name != "nt":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            proc.terminate()
    else:
        proc.terminate()
    proc.join(CONVERT_GRACE_SECONDS)
    if proc.is_alive():
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                proc.kill()
        else:
            proc.kill()
        proc.join(CONVERT_GRACE_SECONDS)
    if proc.is_alive():
        raise RuntimeError("Conversion process could not be stopped")


def run_isolated(job_dir: Path, source_path: Path, *, page_numbers: list[int] | None,
                 ocr: bool, selected_formats: frozenset[str], docx_warnings: bool,
                 child_target=_child_main, cancel_event: threading.Event | None = None) -> ConversionSummary:
    """Drain IPC concurrently; the deadline covers transfer and process exit.

    A receiver thread keeps even a partial pipe frame from blocking supervision.
    All connections and process handles close after the child is stopped.
    """
    started = time.monotonic()
    deadline = started + CONVERT_TIMEOUT_SECONDS
    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=child_target,
        args=(child_conn, str(job_dir), str(source_path), page_numbers, ocr,
              selected_formats, docx_warnings, CONVERT_MEMORY_LIMIT_MB), daemon=True)
    received: Future = Future()
    receiver = None
    summary = ConversionSummary(ok=False, error_kind="crash")

    def receive():
        try:
            value = pickle.loads(parent_conn.recv_bytes(MAX_IPC_BYTES))
            if not isinstance(value, ConversionSummary):
                raise ValueError("Unexpected child response")
            received.set_result(value)
        except Exception:
            received.set_result(ConversionSummary(ok=False, error_kind="crash"))

    try:
        proc.start()
        child_conn.close()
        receiver = threading.Thread(target=receive, name="conversion-result", daemon=True)
        receiver.start()
        while True:
            if cancel_event is not None and cancel_event.is_set():
                summary = ConversionSummary(ok=False, error_kind="cancelled")
                break
            if received.done() and not proc.is_alive():
                summary = received.result()
                break
            if time.monotonic() >= deadline:
                summary = ConversionSummary(ok=False, error_kind="timeout")
                break
            proc.join(min(.025, max(0, deadline - time.monotonic())))
        if summary.ok and summary.details_in_file:
            with (job_dir / "conversion-summary.json").open("rb") as stream:
                payload = stream.read(MAX_IPC_BYTES + 1)
            if len(payload) > MAX_IPC_BYTES:
                raise ValueError("Summary exceeds budget")
            summary = ConversionSummary(**json.loads(payload))
        return summary
    except (OSError, ValueError, TypeError):
        summary = ConversionSummary(ok=False, error_kind="crash")
        return summary
    finally:
        child_conn.close()
        if proc.pid is not None:
            _stop_process(proc)
            proc.join()
        if receiver is not None:
            receiver.join(CONVERT_GRACE_SECONDS)
        parent_conn.close()
        proc.close()
        logger.info("conversion_finished job_id=%s result=%s duration_seconds=%.3f memory_backend=%s",
                    job_dir.name, "complete" if summary.ok else summary.error_kind,
                    time.monotonic() - started, summary.memory_backend or "unknown")


def prune_old_jobs(output_root: Path, retention_hours: float, *, now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    removed = []
    if not output_root.is_dir():
        return removed
    for job_dir in output_root.iterdir():
        if not job_dir.is_dir() or job_dir.is_symlink() or getattr(job_dir, "is_junction", lambda: False)():
            continue
        try:
            metadata = read_metadata(job_dir)
            if metadata:
                expired = metadata["expires_at"] <= now or metadata.get("state") != "complete"
            else:
                newest = max((p.stat().st_mtime for p in job_dir.rglob("*") if p.is_file()),
                             default=job_dir.stat().st_mtime)
                expired = newest <= now - retention_hours * 3600
            if not expired:
                continue
            lease = FileLease(job_dir / ".active.lock")
        except (FileNotFoundError, PermissionError, BlockingIOError):
            continue
        except OSError as exc:
            logger.warning("cleanup_scan_failed job_id=%s error_type=%s", job_dir.name, type(exc).__name__)
            continue
        lease.close()  # Windows cannot remove an open lock file; old IDs are never reused.
        if remove_job(output_root, job_dir):
            removed.append(job_dir.name)
    return removed


async def cleanup_loop(output_root: Path, retention_hours: float, interval_seconds: float) -> None:
    # The lifespan awaits the initial sweep before serving requests.
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(prune_old_jobs, output_root, retention_hours)
        except OSError as exc:
            logger.error("cleanup_sweep_failed error_type=%s", type(exc).__name__)
