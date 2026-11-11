"""Run the declared Chromium workflow against a temporary local server."""
from pathlib import Path
from scripts.check_release import check_browser


if __name__ == "__main__":
    output = Path(".generated/release-check").resolve()
    output.mkdir(parents=True, exist_ok=True)
    check_browser(output, [])
