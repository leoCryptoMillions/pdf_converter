"""Regressions for the concrete failures in the 2026-11-10 audit."""
import asyncio
import base64
import json
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from apps import local_review_ui as ui
from apps.conversion_isolation import ConversionSummary, prune_old_jobs
from apps.job_store import FileLease, create_job, read_metadata, write_metadata
from apps.runtime_config import RuntimeConfig

pytestmark = pytest.mark.mvp


@pytest.fixture(autouse=True)
def isolated_output(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "OUTPUT_ROOT", tmp_path / "jobs")
    monkeypatch.setattr(ui, "_convert_semaphore", asyncio.Semaphore(1))


@pytest.mark.parametrize("variable,value", [
    ("CONVERT_TIMEOUT_SECONDS", "nan"), ("RETENTION_HOURS", "-1"),
    ("CONVERT_MEMORY_LIMIT_MB", "0"), ("CONVERT_CONCURRENCY", "2"),
    ("CLEANUP_INTERVAL_SECONDS", "inf"), ("PORT", "70000"), ("HOST", "0.0.0.0"),
])
def test_invalid_runtime_configuration_is_rejected(monkeypatch, variable, value):
    monkeypatch.setenv("APP_MODE", "local")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValueError):
        RuntimeConfig.from_environment()


@pytest.mark.parametrize("username,password", [("audit", ""), ("", "synthetic"), ("", "")])
def test_remote_configuration_requires_both_credentials(monkeypatch, username, password):
    monkeypatch.setenv("APP_MODE", "remote")
    monkeypatch.setenv("AUTH_USERNAME", username)
    monkeypatch.setenv("AUTH_PASSWORD", password)
    with pytest.raises(ValueError, match="both"):
        RuntimeConfig.from_environment()


def test_partial_auth_and_unicode_do_not_bypass_or_crash(monkeypatch):
    client = TestClient(ui.app)
    monkeypatch.setattr(ui, "AUTH_USERNAME", "audit")
    monkeypatch.setattr(ui, "AUTH_PASSWORD", None)
    assert client.get("/").status_code == 401
    monkeypatch.setattr(ui, "AUTH_PASSWORD", "synthetic")
    encoded = base64.b64encode("ñ:synthetic".encode()).decode()
    response = client.get("/", headers={"Authorization": "Basic " + encoded})
    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "no-store"
    assert client.get("/", auth=("audit", "synthetic")).status_code == 200
    assert client.get("/download/" + "a"*32 + "/result.txt").status_code == 401
    assert client.get("/", headers={"Authorization": "Basic %%%%"}).status_code == 401


def test_local_mode_refuses_foreign_host_and_cross_site_form():
    client = TestClient(ui.app)
    assert client.get("/", headers={"Host": "foreign.example"}).status_code == 403
    assert client.post("/convert", headers={"Origin": "https://foreign.example"}).status_code == 403
    assert client.post("/convert", headers={"Origin": "null", "Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.post("/convert", headers={"Origin": "null", "Sec-Fetch-Site": "same-origin"}).status_code == 400
    assert client.post("/convert", headers={"Origin": "https://testserver"}).status_code == 403
    assert client.post("/convert", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.post("/convert", headers={"Origin": "http://[invalid"}).status_code == 403


def test_local_mode_refuses_remote_peer_even_with_loopback_host():
    client = TestClient(ui.app, base_url="http://127.0.0.1", client=("192.0.2.1", 12345))
    assert client.get("/", headers={"Host": "127.0.0.1"}).status_code == 403


def test_streaming_upload_limit_stops_before_remaining_body(monkeypatch):
    monkeypatch.setattr(ui, "MAX_UPLOAD_BYTES", 1024)
    consumed = []

    async def body():
        chunks = [b'--audit\r\nContent-Disposition: form-data; name="file"; filename="source.pdf"\r\n'
                  b'Content-Type: application/pdf\r\n\r\n', b'x' * 2048,
                  b'\r\n--audit\r\nContent-Disposition: form-data; name="formats"\r\n\r\ntxt\r\n--audit--\r\n']
        for index, chunk in enumerate(chunks):
            consumed.append(index)
            yield chunk

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui.app), base_url="http://localhost") as client:
            return await client.post("/convert", content=body(), headers={"Content-Type": "multipart/form-data; boundary=audit"})

    response = asyncio.run(run())
    assert response.status_code == 413
    assert consumed == [0, 1]
    assert not list(ui.OUTPUT_ROOT.glob("*/source.pdf"))
    assert not ui._convert_semaphore.locked()


def test_exact_file_limit_is_accepted_and_next_byte_rejected(monkeypatch, synthetic_invoice):
    body = synthetic_invoice.read_bytes()
    monkeypatch.setattr(ui, "MAX_UPLOAD_BYTES", len(body))
    client = TestClient(ui.app)
    response = client.post("/convert", files={"file": ("source.pdf", body)}, data={"formats": "txt"})
    assert response.status_code == 200
    response = client.post("/convert", files={"file": ("source.pdf", body + b" ")}, data={"formats": "txt"})
    assert response.status_code == 413
    assert len(list(ui.OUTPUT_ROOT.glob("*/source.pdf"))) == 1


def test_extra_files_are_rejected_before_persisting():
    response = TestClient(ui.app).post("/convert", files=[
        ("file", ("a.pdf", b"%PDF-")), ("extra", ("b.pdf", b"%PDF-"))], data={"formats": "txt"})
    assert response.status_code == 400
    assert not list(ui.OUTPUT_ROOT.glob("*/source.pdf"))


def test_admission_lock_protects_other_server_processes():
    ui.OUTPUT_ROOT.mkdir()
    with FileLease(ui.OUTPUT_ROOT / ".admission.lock"):
        response = TestClient(ui.app).post("/convert", files={"file": ("a.pdf", b"%PDF-")}, data={"formats": "txt"})
        assert response.status_code == 409
    assert not list(ui.OUTPUT_ROOT.glob("*/source.pdf"))


@pytest.mark.parametrize("budget", ["total", "free_disk"])
def test_storage_admission_refuses_without_consuming_pdf(monkeypatch, budget):
    from dataclasses import replace
    from types import SimpleNamespace
    from apps import job_store
    if budget == "total":
        monkeypatch.setattr(job_store, "settings", replace(job_store.settings, max_storage_bytes=1))
    else:
        monkeypatch.setattr(job_store.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    response = TestClient(ui.app).post("/convert", files={"file": ("a.pdf", b"%PDF-")}, data={"formats": "txt"})
    assert response.status_code == 503
    assert not list(ui.OUTPUT_ROOT.glob("*/source.pdf"))
    assert not ui._convert_semaphore.locked()


def test_cancelled_request_keeps_permit_until_worker_stops(monkeypatch):
    started, release = threading.Event(), threading.Event()

    def blocking(job_dir, source_path, **options):
        started.set()
        assert release.wait(5)
        return ConversionSummary(ok=False, error_kind="cancelled")

    monkeypatch.setattr(ui, "run_isolated", blocking)

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui.app), base_url="http://localhost") as client:
            first = asyncio.create_task(client.post("/convert", files={"file": ("a.pdf", b"%PDF-")}, data={"formats": "txt"}))
            assert await asyncio.to_thread(started.wait, 5)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            try:
                second = await client.post("/convert", files={"file": ("b.pdf", b"%PDF-")}, data={"formats": "txt"})
                assert second.status_code == 409
                assert ui._convert_semaphore.locked()
            finally:
                release.set()
            tasks = list(ui._active_conversions)
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(0)
            assert not ui._convert_semaphore.locked()

    asyncio.run(run())
    assert not list(ui.OUTPUT_ROOT.glob("*/source.pdf"))


def test_failed_export_does_not_publish_partial_results(monkeypatch):
    def fail(job_dir, source_path, **options):
        staging = job_dir / ".staging"
        staging.mkdir()
        (staging / "result.xlsx").write_bytes(b"partial")
        return ConversionSummary(ok=False, error_kind="export_value_error")
    monkeypatch.setattr(ui, "run_isolated", fail)
    response = TestClient(ui.app).post("/convert", files={"file": ("a.pdf", b"%PDF-")}, data={"formats": "xlsx"})
    assert response.status_code == 400
    assert not list(ui.OUTPUT_ROOT.glob("*/result.xlsx"))
    assert not list(ui.OUTPUT_ROOT.glob("*/.staging"))


def test_expired_download_is_denied_and_active_job_is_not_pruned():
    job, lease = create_job(ui.OUTPUT_ROOT, 24)
    artifacts = job / "artifacts"
    artifacts.mkdir()
    (artifacts / "result.txt").write_text("synthetic")
    metadata = read_metadata(job)
    metadata.update(state="complete", expires_at=time.time() - 1)
    write_metadata(job, metadata)
    response = TestClient(ui.app).get(f"/download/{job.name}/result.txt")
    assert response.status_code == 410
    assert response.headers["Cache-Control"] == "no-store"
    assert prune_old_jobs(ui.OUTPUT_ROOT, 24) == []
    lease.close()
    assert prune_old_jobs(ui.OUTPUT_ROOT, 24) == [job.name]


def test_lifespan_sweeps_orphaned_jobs_before_serving():
    job, lease = create_job(ui.OUTPUT_ROOT, 24)
    lease.close()  # Simulate an interrupted server, with metadata still running.
    with TestClient(ui.app) as client:
        assert client.get("/health").status_code == 200
        assert not job.exists()


def test_nested_warnings_are_visible_with_provenance(tmp_path):
    import re
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    source = tmp_path / "merged.pdf"
    drawing = canvas.Canvas(str(source))
    table = Table([["Merged header", ""], ["A", "B"]], colWidths=[120, 120])
    table.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("GRID", (0, 0), (-1, -1), 1, (0, 0, 0))]))
    table.wrapOn(drawing, 400, 400)
    table.drawOn(drawing, 50, 650)
    drawing.save()
    client = TestClient(ui.app)
    response = client.post("/convert", files={"file": ("synthetic.pdf", source.read_bytes())}, data={"formats": ["xlsx", "docx", "txt"]})
    assert response.status_code == 200
    assert "MISSING_OR_MERGED_CELL" in response.text
    assert "Descargas disponibles hasta" in response.text
    report_link = re.search(r'href="([^"]+/warnings.json)"', response.text)[1]
    report = client.get(report_link)
    assert report.headers["Cache-Control"] == "no-store"
    issues = report.json()
    cell_issue = next(w for w in issues if w["code"] == "MISSING_OR_MERGED_CELL")
    assert cell_issue["table_id"] == "p1_t1"
    assert cell_issue["row_index"] == 0
    assert cell_issue["col_index"] == 1
    assert len({json.dumps(w, sort_keys=True) for w in issues}) == len(issues)
