"""F0 local web wrapper (apps/local_review_ui.py): real upload -> convert ->
download, through the actual HTTP routes, no mocks.
"""
import pytest
from fastapi.testclient import TestClient

from apps import local_review_ui
from apps.local_review_ui import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_output(tmp_path, monkeypatch):
    monkeypatch.setattr(local_review_ui, "OUTPUT_ROOT", tmp_path / "web_ui")


@pytest.mark.mvp
def test_index_serves_the_upload_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "Convertir" in response.text


@pytest.mark.mvp
def test_convert_and_download_round_trip(synthetic_invoice):
    with synthetic_invoice.open("rb") as handle:
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


@pytest.mark.mvp
def test_rejects_non_pdf_upload():
    response = client.post("/convert", files={"file": ("x.txt", b"not a pdf", "text/plain")},
                            data={"formats": ["xlsx"]})
    assert response.status_code == 400
    assert "Conversi" in response.text


@pytest.mark.mvp
def test_download_rejects_path_traversal():
    response = client.get("/download/anything/../../pyproject.toml")
    assert response.status_code == 404


@pytest.mark.parametrize("pages", ["0", "1,1", "1,,2", "1,", "-1", "1-3", "abc"])
def test_invalid_pages_preserve_options(pages):
    response = client.post(
        "/convert", files={"file": ("sample.pdf", b"%PDF-", "application/pdf")},
        data={"formats": ["docx"], "pages": pages, "ocr": "1"},
    )
    assert response.status_code == 400
    assert f'value="{pages}"' in response.text
    assert 'value="docx" aria-describedby="formats-error" checked' in response.text
    assert 'name="ocr" value="1" checked' in response.text
    assert "Conservamos las opciones" in response.text


@pytest.mark.mvp
def test_no_formats_requires_an_explicit_selection():
    response = client.post("/convert", files={"file": ("sample.pdf", b"%PDF-", "application/pdf")})
    assert response.status_code == 400
    assert "Selecciona al menos un formato" in response.text


@pytest.mark.mvp
def test_result_displays_safe_filename_preview_and_all_formats(synthetic_invoice):
    with synthetic_invoice.open("rb") as handle:
        response = client.post(
            "/convert", files={"file": ('<script>alert(1)</script>.pdf', handle, "application/pdf")},
            data={"formats": ["xlsx", "docx", "txt"]},
        )
    assert response.status_code == 200
    assert "&lt;script&gt;alert(1)&lt;/script&gt;.pdf" in response.text
    assert "<script>alert(1)</script>" not in response.text
    assert 'class="text-preview"' in response.text
    import re
    for link in re.findall(r'href="(/download/[a-f0-9]+/[^"]+)"', response.text):
        assert client.get(link).status_code == 200


@pytest.mark.mvp
def test_error_escapes_page_input():
    response = client.post(
        "/convert", files={"file": ("sample.pdf", b"%PDF-", "application/pdf")},
        data={"formats": ["txt"], "pages": '\"><script>alert(1)</script>'},
    )
    assert response.status_code == 400
    assert "<script>alert(1)</script>" not in response.text


def test_local_assets_are_served():
    for name in ("app.js", "theme.js", "help.js", "style.css", "help.css"):
        assert client.get(f"/assets/{name}").status_code == 200


@pytest.mark.parametrize("url", ["/", "/assets/theme.js", "/download/missing/result.txt"])
@pytest.mark.mvp
def test_local_response_headers_cover_pages_assets_and_errors(url):
    response = client.get(url)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    policy = response.headers["Content-Security-Policy"]
    assert "script-src 'self'" in policy
    assert "form-action 'self'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "unsafe-inline" not in policy


def test_help_center_and_mascot_are_available():
    response = client.get("/ayuda")
    assert response.status_code == 200
    assert "Preguntas frecuentes" in response.text
    assert 'id="guia"' in response.text
    assert 'id="topic-ocr"' in response.text
    assert 'id="help-topic-convert"' in response.text
    image = client.get("/assets/pdf-converter-guide.png")
    assert image.status_code == 200
    assert image.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_help_search_works_without_javascript_and_escapes_input():
    response = client.get("/ayuda", params={"q": "CONTRASENA"})
    assert response.status_code == 200
    assert 'id="topic-upload" data-faq-item open ' in response.text
    assert 'id="topic-theme" data-faq-item  hidden' in response.text
    response = client.get("/ayuda", params={"q": '\"><script>alert(1)</script>'})
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_converter_exposes_context_help_with_native_links():
    response = client.get("/")
    assert 'href="/ayuda#topic-convert"' in response.text
    assert 'href="/ayuda#topic-remove"' in response.text
    assert 'id="context-dialog"' in response.text


@pytest.mark.parametrize('annex', [False, True])
@pytest.mark.mvp
def test_word_download_layout_notes_and_optional_annex_are_consistent(annex, synthetic_invoice):
    import re
    from io import BytesIO
    from docx import Document
    with synthetic_invoice.open('rb') as handle:
        response = client.post('/convert', files={'file': ('sample.pdf', handle, 'application/pdf')},
            data={'formats': ['docx'], 'docx_warnings': '1' if annex else ''})
    assert response.status_code == 200
    links = re.findall(r'href="(/download/[a-f0-9]+/[^"]+)"', response.text)
    word = Document(BytesIO(client.get(next(l for l in links if l.endswith('result.docx'))).content))
    assert any(p.text == 'Conversion warnings' for p in word.paragraphs) is annex
    data = client.get(next(l for l in links if l.endswith('document.ir.json'))).json()
    assert data['extraction_options']['preserve_layout'] is True
    assert any(w['code'] == 'DOCX_LAYOUT_APPROXIMATE' for p in data['pages'] for w in p['warnings'])
    assert 'no reconstruye el diseño exacto ni las imágenes' not in response.text


def test_error_preserves_word_annex_preference():
    response = client.post('/convert', files={'file': ('source.pdf', b'%PDF-', 'application/pdf')},
        data={'formats': ['docx'], 'pages': '0', 'docx_warnings': '1'})
    assert response.status_code == 400
    assert 'name="docx_warnings" value="1" checked' in response.text
