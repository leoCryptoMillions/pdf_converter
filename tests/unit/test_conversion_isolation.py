"""apps/conversion_isolation.py: process isolation, hard timeout, memory cap
and TTL cleanup. Real subprocesses and real file mtimes, no mocks for the
behavior under test - only the module's timing constants are shortened via
monkeypatch so the suite stays fast.
"""
import os
import sys
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


@pytest.mark.skipif(os.name == "nt", reason="RLIMIT_AS is POSIX-only")
@pytest.mark.mvp
def test_run_isolated_reports_memory_error_as_clean_failure(tmp_path):
    summary = run_isolated(
        tmp_path, tmp_path / "source.pdf", page_numbers=None, ocr=False,
        selected_formats=frozenset(), docx_warnings=False, child_target=_memory_hog_child,
    )
    assert summary.ok is False
    assert summary.error_kind == "memory"
    assert "Traceback" not in summary.error_message


def test_apply_memory_limit_is_a_noop_without_resource_module(monkeypatch):
    monkeypatch.setitem(sys.modules, "resource", None)
    _apply_memory_limit(768)  # must not raise


def test_apply_memory_limit_is_a_noop_for_non_positive_limit():
    _apply_memory_limit(0)  # must not raise or attempt to import resource
