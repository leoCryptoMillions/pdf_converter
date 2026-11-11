"""One reproducible release check; all document inputs are synthetic.

python -m scripts.check_release [--skip-browser] [--audit]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


def run_step(name: str, command: list[str], report: list, **kwargs):
    print(f"Checking {name}...", flush=True)
    start = time.monotonic()
    result = subprocess.run(command, **kwargs)
    report.append({"step": name, "exit_code": result.returncode,
                   "seconds": round(time.monotonic() - start, 2)})
    if result.returncode:
        raise RuntimeError(f"{name} failed (exit {result.returncode})")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-browser", action="store_true", help="Partial check; does not certify browser behavior")
    parser.add_argument("--audit", action="store_true", help="Query vulnerability data and write a CycloneDX SBOM")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    output = root / ".generated/release-check"
    output.mkdir(parents=True, exist_ok=True)
    report = {"passed": False, "browser_checked": not args.skip_browser,
              "vulnerability_audit": args.audit, "steps": []}
    try:
        run_step("dependency consistency", [sys.executable, "-m", "pip", "check"], report["steps"])
        coverage_env = dict(os.environ, COVERAGE_FILE=str(output / ".coverage"))
        run_step("coverage reset", [sys.executable, "-m", "coverage", "erase"], report["steps"], env=coverage_env)
        run_step("complete regression and coverage", [sys.executable, "-m", "pytest", "-q",
            "-m", "mvp or not mvp", "--show-capture=no", "--cov=apps", "--cov=packages",
            "--cov-branch", f"--cov-report=json:{output / 'coverage.json'}",
            "--cov-report=term", "--cov-fail-under=70"], report["steps"], env=coverage_env)
        run_step("runtime dependency inventory", [sys.executable, "-m", "benchmarks.dependency_inventory", "--profile", "mvp"], report["steps"])
        run_step("wheel build", [sys.executable, "-m", "build", "--wheel", "--no-isolation",
            "--outdir", str(output / "dist")], report["steps"])
        run_step("clean installed wheel", [sys.executable, "-m", "scripts.check_install"], report["steps"])
        if args.audit:
            run_step("vulnerability audit and SBOM", [sys.executable, "-m", "pip_audit", "-r", "requirements-mvp.lock",
                "--no-deps", "--disable-pip", "--format", "cyclonedx-json", "--output", str(output / "sbom.json")], report["steps"])
        if not args.skip_browser:
            check_browser(output, report["steps"])
        report["passed"] = True
    except (RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["passed"] else 1


def check_browser(output: Path, report: list):
    from benchmarks.generate_synthetic_adversarial import build_base_pdf
    sample = output / "synthetic.pdf"
    build_base_pdf(sample)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = dict(os.environ, APP_MODE="local", HOST="127.0.0.1", PORT=str(port),
               PDF_UI_URL=f"http://127.0.0.1:{port}", PDF_UI_SAMPLE=str(sample))
    env.pop("AUTH_USERNAME", None)
    env.pop("AUTH_PASSWORD", None)
    with (output / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.local_review_ui:app",
            "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], env=env,
            stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("Browser test server exited; inspect .generated/release-check/server.log")
                try:
                    with urlopen(env["PDF_UI_URL"] + "/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(.1)
            else:
                raise RuntimeError("Browser test server did not become ready")
            run_step("browser conversion workflow", ["node", "tests/e2e/local_review_ui.cjs"], report, env=env)
            run_step("dashboard save/cancel/export", ["node", "tests/e2e/gaps_dashboard.cjs"], report, env=env)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
