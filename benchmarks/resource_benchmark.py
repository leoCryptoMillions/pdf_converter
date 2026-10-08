"""Measure cold subprocesses and sampled process-tree resources; no tariff assumptions."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time


def run_worker(route: str, file_id: str, page: int) -> None:
    from benchmarks.common import load_manifest
    row = next(r for r in load_manifest() if r.file_id == file_id)
    if not row.authorized:
        raise ValueError("Unauthorized source")
    if route == "digital":
        from packages.converters.digital import extract_digital
        from packages.exporters.xlsx import export_xlsx
        data = export_xlsx(extract_digital(row.pdf_path, page_numbers=[page]))
        if not data:
            raise ValueError("Empty artifact")
    else:
        from benchmarks.validate_prototype import ocr_page_text
        if not ocr_page_text(row.pdf_path, page):
            raise ValueError("Empty OCR result")


def measure(route: str, file_id: str, page: int, *, timeout_s: float = 180) -> dict:
    import psutil
    command = [sys.executable, "-m", "benchmarks.resource_benchmark", "--worker", route,
               "--file-id", file_id, "--page", str(page)]
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    root = psutil.Process(process.pid)
    peak_rss = 0
    sampled_cpu = {}
    timeout = False
    while process.poll() is None:
        if time.monotonic() - started > timeout_s:
            timeout = True
            try:
                for child in root.children(recursive=True):
                    child.kill()
            except psutil.Error:
                pass
            process.kill()
            break
        try:
            alive = [root, *root.children(recursive=True)]
            rss = 0
            for child in alive:
                try:
                    rss += child.memory_info().rss
                    cpu = child.cpu_times()
                    sampled_cpu[(child.pid, child.create_time())] = cpu.user + cpu.system
                except psutil.Error:
                    pass
            peak_rss = max(peak_rss, rss)
        except psutil.Error:
            pass
        time.sleep(0.02)
    process.wait(timeout=10)
    return {"route": route, "file_id": file_id, "page": page, "wall_seconds": time.monotonic() - started,
            "sampled_tree_cpu_seconds": sum(sampled_cpu.values()), "sampled_tree_peak_rss_mib": peak_rss / 1024 ** 2,
            "success": process.returncode == 0 and not timeout, "timed_out": timeout}


def cost_scenarios(seconds_per_page: float, pages: list[int] = [1000, 10000, 100000],
                   hourly_rate: float | None = None, fixed_monthly: float | None = None) -> list[dict]:
    if (not math.isfinite(seconds_per_page) or seconds_per_page < 0 or
        any(not math.isfinite(value) or value < 0 for value in (hourly_rate, fixed_monthly) if value is not None) or
        any(type(count) is not int or count < 0 for count in pages)):
        raise ValueError("Nonnegative inputs required")
    return [{"pages_month": count, "sequential_worker_hours": count * seconds_per_page / 3600,
             "compute_cost_estimate": None if hourly_rate is None else count * seconds_per_page / 3600 * hourly_rate,
             "total_estimate": None if hourly_rate is None or fixed_monthly is None else
                 count * seconds_per_page / 3600 * hourly_rate + fixed_monthly,
             "exclusions": "storage, transfer, licenses, operations, load/concurrency and unknown infrastructure"} for count in pages]


def run(repetitions: int = 3) -> dict:
    import psutil
    if repetitions < 1:
        raise ValueError("At least one repetition required")
    results = []
    for route, file_id, page in [("digital", "synthetic_digital_001", 1), ("ocr", "scanned_002", 3)]:
        for _ in range(repetitions):
            results.append(measure(route, file_id, page))
    summaries = []
    for route in ("digital", "ocr"):
        successful = [r for r in results if r["route"] == route and r["success"]]
        elapsed = sorted(r["wall_seconds"] for r in successful)
        summaries.append({"route": route, "successful_samples": len(successful),
                          "wall_mean_seconds": sum(elapsed) / len(elapsed) if elapsed else None,
                          "observed_max_seconds": max(elapsed) if elapsed else None,
                          "peak_rss_mib": max((r["sampled_tree_peak_rss_mib"] for r in successful), default=None),
                          "scenarios": cost_scenarios(sum(elapsed) / len(elapsed)) if elapsed else []})
    report = {"scope": "cold sequential one-page subprocesses; includes interpreter/import/render/native child time; no queue/storage/network",
              "limitations": "20 ms sampling can miss short-lived child CPU/RSS; no p95 claim with three samples; RSS sum may count shared memory",
              "hardware": {"platform": platform.platform(), "cpu": platform.processor(),
                           "logical_cpus": psutil.cpu_count(), "physical_cpus": psutil.cpu_count(logical=False),
                           "ram_gib": psutil.virtual_memory().total / 1024 ** 3},
              "results": results, "summaries": summaries, "cost_status": "Tariffs unknown; currency estimates null"}
    out = Path(".generated/f0/resources")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=["digital", "ocr"])
    parser.add_argument("--file-id")
    parser.add_argument("--page", type=int, default=1)
    args = parser.parse_args()
    if args.worker:
        run_worker(args.worker, args.file_id, args.page)
    else:
        print(json.dumps(run(), indent=2))
