"""Install the wheel into a fresh runtime-only venv and test outside the source tree."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import uuid
import venv


def main():
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / ".generated/release-check/dist").glob("pdf_converter-*.whl"))
    if not wheels:
        raise RuntimeError("Build the wheel first: python -m build --wheel --outdir .generated/release-check/dist")
    wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    work = root / ".generated/release-check" / ("installed-" + uuid.uuid4().hex[:12])
    work.mkdir(parents=True)
    env_dir = work / "venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--require-hashes", "-r", str(root / "requirements-mvp.lock")], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], check=True)
    probe = work / "installed_smoke.py"
    shutil.copyfile(root / "scripts/installed_smoke.py", probe)
    env = dict(os.environ, APP_MODE="local", HOST="127.0.0.1")
    for key in ("PYTHONPATH", "AUTH_USERNAME", "AUTH_PASSWORD", "COVERAGE_PROCESS_START", "COVERAGE_FILE"):
        env.pop(key, None)
    subprocess.run([str(python), str(probe)], cwd=work, env=env, check=True)
    print(f"PASS: clean installed wheel; evidence in {work}")


if __name__ == "__main__":
    main()
