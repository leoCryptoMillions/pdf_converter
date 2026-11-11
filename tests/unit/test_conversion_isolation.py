"""apps/conversion_isolation.py: process isolation, hard timeout, memory cap
and TTL cleanup. Real subprocesses and real file mtimes, no mocks for the
behavior under test - only the module's timing constants are shortened via
monkeypatch so the suite stays fast.
"""
import os
import time

import pytest

from apps import conversion_isolation
from apps.conversion_isolation import ConversionSummary, _apply_memory_limit, prune_old_jobs, run_isolated


def _slow_child(conn, job_dir, source_path, page_numbers, ocr, selected_formats,
                 docx_warnings, memory_limit_mb):
    time.sleep(10)
    conn.send(ConversionSummary(ok=True))


def _memory_hog_child(conn, job_dir, source_path, page_numbers, ocr, selected_formats,
                       docx_warnings, memory_limit_mb):
    _apply_memory_limit(memory_limit_mb)
    try:
        _ = bytearray(200 * 1024 * 1024)
        conn.send(ConversionSummary(ok=True))
    except MemoryError:
        conn.send(ConversionSummary(ok=False, error_kind="memory", error_message="memory limit exceeded"))
    finally:
        conn.close()


@pytest.mark.mvp
def test_prune_old_jobs_removes_only_stale_dirs(tmp_path):
    now = time.time()
    stale = tmp_path / "stale_job"
    fresh = tmp_path / "fresh_job"
    stale.mkdir()
    fresh.mkdir()
    (stale / "result.txt").write_text("old")
    (fresh / "result.txt").write_text("new")
    os.utime(stale / "result.txt", (now - 48 * 3600, now - 48 * 3600))
    os.utime(fresh / "result.txt", (now, now))

    removed = prune_old_jobs(tmp_path, retention_hours=24, now=now)

    assert removed == ["stale_job"]
    assert not stale.exists()
    assert fresh.exists()


@pytest.mark.mvp
def test_prune_old_jobs_handles_missing_root(tmp_path):
    assert prune_old_jobs(tmp_path / "does_not_exist", retention_hours=24) == []


@pytest.mark.mvp
def test_run_isolated_times_out_and_kills_child(tmp_path, monkeypatch):
    monkeypatch.setattr(conversion_isolation, "CONVERT_TIMEOUT_SECONDS", 0.3)
    monkeypatch.setattr(conversion_isolation, "CONVERT_GRACE_SECONDS", 0.3)

    summary = run_isolated(
        tmp_path, tmp_path / "source.pdf", page_numbers=None, ocr=False,
        selected_formats=frozenset(), docx_warnings=False, child_target=_slow_child,
    )

    assert summary.ok is False
    assert summary.error_kind == "timeout"


@pytest.mark.mvp
def test_run_isolated_reports_memory_error_as_clean_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(conversion_isolation, "CONVERT_MEMORY_LIMIT_MB", 96)
    summary = run_isolated(
        tmp_path, tmp_path / "source.pdf", page_numbers=None, ocr=False,
        selected_formats=frozenset(), docx_warnings=False, child_target=_memory_hog_child,
    )
    assert summary.ok is False
    assert summary.error_kind == "memory"
    assert "Traceback" not in summary.error_message


def test_apply_memory_limit_rejects_non_positive_limit():
    with pytest.raises(ValueError, match="positive"):
        _apply_memory_limit(0)


def _large_summary_child(conn, *args):
    conn.send(ConversionSummary(ok=True, warnings=[
        {"code": "TEST", "page_number": i, "message": "x" * 256 + str(i)} for i in range(1000)]))
    conn.close()


def _crash_child(conn, *args):
    conn.close()


@pytest.mark.mvp
def test_large_summary_is_drained_before_child_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(conversion_isolation, "CONVERT_TIMEOUT_SECONDS", 5)
    summary = run_isolated(tmp_path, tmp_path / "source.pdf", page_numbers=None,
        ocr=False, selected_formats=frozenset(), docx_warnings=False, child_target=_large_summary_child)
    assert summary.ok
    assert len(summary.warnings) == 1000


@pytest.mark.mvp
def test_child_eof_is_a_controlled_failure(tmp_path):
    summary = run_isolated(tmp_path, tmp_path / "source.pdf", page_numbers=None,
        ocr=False, selected_formats=frozenset(), docx_warnings=False, child_target=_crash_child)
    assert not summary.ok
    assert summary.error_kind == "crash"


def _unicode_warning_child(conn, *args):
    from packages.converters import digital
    from packages.document_ir.models import ContentWarning
    extract = digital.extract_digital

    def with_warnings(*positional, **options):
        document = extract(*positional, **options)
        document.warnings.extend(ContentWarning(level="warning", code=f"UNICODE_{i}",
            message="🔎" * 2000, page_number=1) for i in range(200))
        return document

    digital.extract_digital = with_warnings
    conversion_isolation._child_main(conn, *args)


@pytest.mark.mvp
def test_unicode_warning_budget_preserves_complete_download(tmp_path, synthetic_invoice):
    import json
    summary = run_isolated(tmp_path, synthetic_invoice, page_numbers=None, ocr=False,
        selected_formats=frozenset({"txt"}), docx_warnings=False, child_target=_unicode_warning_child)
    assert summary.ok
    assert summary.warning_count >= 200
    assert len(summary.warnings) < 200
    assert (tmp_path / "conversion-summary.json").stat().st_size <= conversion_isolation.MAX_IPC_BYTES
    report = json.loads((tmp_path / ".staging" / "warnings.json").read_text(encoding="utf-8"))
    assert len(report) == summary.warning_count
    assert sum(w["code"].startswith("UNICODE_") for w in report) == 200
    assert next(w for w in report if w["code"] == "UNICODE_199")["message"] == "🔎" * 2000
