"""Validated configuration for the supported, single-user MVP."""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import math
import os


def positive_number(name: str, default: str, *, integer: bool = False) -> float | int:
    raw = os.environ.get(name, default)
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a positive {'integer' if integer else 'number'}") from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def is_loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    host: str
    port: int
    username: str | None
    password: str | None
    timeout: float
    grace: float
    memory_mb: int
    retention_hours: float
    cleanup_interval: float
    max_storage_bytes: int
    max_job_bytes: int
    min_free_bytes: int

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        mode = os.environ.get("APP_MODE", "local").lower()
        if mode not in {"local", "remote"}:
            raise ValueError("APP_MODE must be local or remote")
        host = os.environ.get("HOST", "127.0.0.1" if mode == "local" else "0.0.0.0")
        if mode == "local" and not is_loopback(host):
            raise ValueError("Local mode requires a loopback HOST; set APP_MODE=remote for network access")
        user, password = os.environ.get("AUTH_USERNAME"), os.environ.get("AUTH_PASSWORD")
        if bool(user) != bool(password) or (mode == "remote" and not (user and password)):
            raise ValueError("Configure both AUTH_USERNAME and AUTH_PASSWORD; remote mode requires them")
        if user and (":" in user or any(ord(c) < 32 for c in user)):
            raise ValueError("AUTH_USERNAME cannot contain colons or control characters")
        for name in ("CONVERT_CONCURRENCY", "WEB_CONCURRENCY", "UVICORN_WORKERS"):
            if positive_number(name, "1", integer=True) != 1:
                raise ValueError(f"{name}=1 is required by the single-user MVP")
        port = positive_number("PORT", "8420", integer=True)
        if port > 65535:
            raise ValueError("PORT must be between 1 and 65535")
        mib = 1024 * 1024
        config = cls(mode, host, port, user, password,
            positive_number("CONVERT_TIMEOUT_SECONDS", "90"),
            positive_number("CONVERT_GRACE_SECONDS", "5"),
            positive_number("CONVERT_MEMORY_LIMIT_MB", "768", integer=True),
            positive_number("RETENTION_HOURS", "24"),
            positive_number("CLEANUP_INTERVAL_SECONDS", "3600"),
            positive_number("MAX_STORAGE_MB", "2048", integer=True) * mib,
            positive_number("MAX_JOB_MB", "512", integer=True) * mib,
            positive_number("MIN_FREE_DISK_MB", "256", integer=True) * mib)
        if config.max_job_bytes < 26 * mib or config.max_storage_bytes < config.max_job_bytes:
            raise ValueError("MAX_JOB_MB must be >=26 and MAX_STORAGE_MB must be >= MAX_JOB_MB")
        return config


settings = RuntimeConfig.from_environment()
