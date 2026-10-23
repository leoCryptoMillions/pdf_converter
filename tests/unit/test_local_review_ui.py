"""F0 local web wrapper (apps/local_review_ui.py): real upload -> convert ->
download, through the actual HTTP routes, no mocks.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from apps.local_review_ui import OUTPUT_ROOT, app

CORPUS_SAMPLE = Path("benchmarks/corpus/files/synthetic_base_invoice.pdf")
client = TestClient(app)


def test_index_serves_the_upload_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "Convertir" in response.text


def test_convert_and_download_round_trip():
    with CORPUS_SAMPLE.open("rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("source.pdf", handle, "application/pdf")},
            data={"formats": ["xlsx", "txt"]},
        )
    assert response.status_code == 200
    assert "needs_review" in response.text

    import re
    links = re.findall(r'href="(/download/[a-f0-9]+/[^"]+)"', response.text)
    assert any(link.endswith("result.xlsx") for link in links)
    assert any(link.endswith("result.txt") for link in links)

    download = client.get(next(link for link in links if link.endswith("result.xlsx")))
    assert download.status_code == 200
    assert download.content.startswith(b"PK")  # XLSX is a zip archive.


def test_rejects_non_pdf_upload():
    response = client.post("/convert", files={"file": ("x.txt", b"not a pdf", "text/plain")},
                            data={"formats": ["xlsx"]})
    assert response.status_code == 400
    assert "Conversi" in response.text


def test_download_rejects_path_traversal():
    response = client.get("/download/anything/../../pyproject.toml")
    assert response.status_code == 404


def teardown_module():
    import shutil
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
