"""Copied beside an isolated venv before running; no source-tree imports."""
from io import BytesIO
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
from zipfile import ZipFile


def synthetic_pdf():
    stream = b"BT /F1 12 Tf 50 700 Td (Audit synthetic 000123) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    body = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(body)
    body += b"xref\n0 6\n0000000000 65535 f \n"
    body += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    return body + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


def main():
    import apps
    from apps.local_review_ui import ASSET_ROOT
    from docx import Document
    from openpyxl import load_workbook
    assert "site-packages" in str(Path(apps.__file__).resolve()).lower()
    for name in ("shell.html", "app.js", "style.css", "theme.js", "help.js", "help.css", "help.json", "pdf-converter-guide.png"):
        assert (ASSET_ROOT / name).is_file(), name
    source = Path("source.pdf")
    source.write_bytes(synthetic_pdf())
    subprocess.run([sys.executable, "-m", "apps.convert", str(source), "--output", "cli-output",
                    "--formats", "docx", "xlsx", "txt"], check=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = dict(os.environ, PORT=str(port))
    base = f"http://127.0.0.1:{port}"
    with Path("server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "apps.local_review_ui"], env=env,
            stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError("Installed server exited")
                try:
                    with urlopen(base + "/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(.1)
            else:
                raise RuntimeError("Installed server did not become ready")
            for name in ("app.js", "style.css", "help.json"):
                with urlopen(base + "/assets/" + name) as response:
                    assert response.status == 200
            boundary = "installed-audit"
            payload = b""
            for fmt in ("docx", "xlsx", "txt"):
                payload += f'--{boundary}\r\nContent-Disposition: form-data; name="formats"\r\n\r\n{fmt}\r\n'.encode()
            payload += f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
            payload += source.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
            request = Request(base + "/convert", data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            with urlopen(request, timeout=120) as response:
                assert response.status == 200
                page = response.read().decode()
                assert response.headers["Cache-Control"] == "no-store"
            links = re.findall(r'href="(/download/[a-f0-9]+/[^\"]+)"', page)
            artifacts = {}
            for link in links:
                with urlopen(base + link) as response:
                    assert response.headers["Cache-Control"] == "no-store"
                    artifacts[link.rsplit("/", 1)[1]] = response.read()
            assert {"result.docx", "result.xlsx", "result.txt", "document.ir.json", "warnings.json"} == set(artifacts)
            assert "000123" in artifacts["result.txt"].decode()
            word = Document(BytesIO(artifacts["result.docx"]))
            assert any("000123" in p.text for p in word.paragraphs)
            word.add_paragraph("Installed edit/save/reopen")
            word.save("edited.docx")
            assert Document("edited.docx").paragraphs[-1].text == "Installed edit/save/reopen"
            excel = load_workbook(BytesIO(artifacts["result.xlsx"]))
            assert "Pagina_1" in excel.sheetnames
            assert not any(cell.data_type == "f" for sheet in excel for row in sheet for cell in row)
            excel.active["A100"] = "Installed edit/save/reopen"
            excel.save("edited.xlsx")
            excel.close()
            reopened = load_workbook("edited.xlsx")
            assert reopened.active["A100"].value == "Installed edit/save/reopen"
            reopened.close()
            Path("report.json").write_text(json.dumps({"passed": True, "installed_from": str(apps.__file__),
                "artifacts": sorted(artifacts), "word_excel_edit_save_reopen": True}, indent=2), encoding="utf-8")
        finally:
            server.terminate()
            server.wait(timeout=10)
    print("PASS: installed assets, CLI, HTTP conversion/downloads and Office file edit/save/reopen")


if __name__ == "__main__":
    main()
