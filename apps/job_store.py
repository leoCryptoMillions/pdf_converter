"""Single-host admission locks, bounded artifacts and explicit job expiry."""
from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
import shutil
import time
import uuid

from apps.runtime_config import settings

logger = logging.getLogger("pdf_converter.jobs")
METADATA = "job.json"


class FileLease:
    """Nonblocking OS lock; shared across server processes using the same directory."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = path.open("a+b")
        try:
            if self.stream.seek(0, 2) == 0:
                self.stream.write(b"\0")
                self.stream.flush()
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.stream.close()
            raise

    def close(self):
        if not self.stream.closed:
            self.stream.close()  # The OS releases the lock, including after a crash.

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def directory_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def ensure_capacity(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if sum(p.is_dir() for p in root.iterdir()) >= 1000:
        raise OSError("retained_jobs_budget")
    if directory_bytes(root) + settings.max_job_bytes > settings.max_storage_bytes:
        raise OSError("storage_budget")
    if shutil.disk_usage(root).free < settings.min_free_bytes + settings.max_job_bytes:
        raise OSError("disk_reserve")


def write_metadata(job_dir: Path, metadata: dict) -> None:
    temporary = job_dir / (METADATA + ".part")
    temporary.write_text(json.dumps(metadata), encoding="utf-8")
    temporary.replace(job_dir / METADATA)


def read_metadata(job_dir: Path) -> dict | None:
    try:
        with (job_dir / METADATA).open("r", encoding="utf-8") as stream:
            data = json.loads(stream.read(8192))
        if (not isinstance(data, dict) or type(data.get("expires_at")) not in (int, float)
                or not math.isfinite(data["expires_at"]) or data["expires_at"] <= 0):
            return None
        return data
    except (OSError, ValueError):
        return None


def create_job(root: Path, retention_hours: float) -> tuple[Path, FileLease]:
    job_dir = root / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=False)
    lease = None
    now = time.time()
    try:
        lease = FileLease(job_dir / ".active.lock")
        write_metadata(job_dir, {"state": "running", "created_at": now,
                                 "expires_at": now + retention_hours * 3600})
    except BaseException:
        if lease:
            lease.close()
        remove_job(root, job_dir)
        raise
    return job_dir, lease


def write_artifact(job_dir: Path, staging: Path, name: str, data: bytes) -> None:
    if directory_bytes(job_dir) + len(data) > settings.max_job_bytes:
        raise OSError("job_budget")
    if shutil.disk_usage(job_dir).free - len(data) < settings.min_free_bytes:
        raise OSError("disk_reserve")
    staging.mkdir(exist_ok=True)
    temporary = staging / (name + ".part")
    temporary.write_bytes(data)
    temporary.replace(staging / name)


def publish_job(job_dir: Path) -> dict:
    metadata = read_metadata(job_dir)
    if metadata is None or metadata["expires_at"] <= time.time():
        raise OSError("job_expired")
    (job_dir / ".staging").replace(job_dir / "artifacts")
    metadata["state"] = "complete"
    write_metadata(job_dir, metadata)
    return metadata


def remove_job(root: Path, job_dir: Path) -> bool:
    """Never follow a symlink/junction or delete outside the designated root."""
    resolved_root, resolved_job = root.resolve(), job_dir.resolve()
    if (job_dir.is_symlink() or getattr(job_dir, "is_junction", lambda: False)() or
            resolved_job.parent != resolved_root):
        logger.warning("cleanup_refused job_id=%s", job_dir.name)
        return False
    try:
        shutil.rmtree(resolved_job)
        return True
    except FileNotFoundError:
        return True
    except OSError as exc:
        logger.warning("cleanup_failed job_id=%s error_type=%s", job_dir.name, type(exc).__name__)
        return False
