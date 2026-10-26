"""Real PDF -> self-contained IR -> editable DOCX, independent of private PDFs."""
import base64
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from PIL import Image
import pytest
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from packages.converters.digital import extract_digital
from packages.document_ir.models import DocumentIR
from packages.exporters.docx import export_docx


@pytest.fixture
def layout_pdf(tmp_path):
    path = tmp_path / 'layout.pdf'
    logo = Image.new('RGB', (120, 40), 'navy')
    pdf = canvas.Canvas(str(path), pagesize=(595, 850))
    pdf.drawImage(ImageReader(logo), 30, 780, width=120, height=40)
    pdf.setFillColor(colors.lightgrey)
    pdf.rect(30, 700, 530, 30, fill=1, stroke=0)
    pdf.setFillColor(colors.blue)
    pdf.setFont('Helvetica-Bold', 13)
    pdf.drawString(40, 710, 'A styled heading')
    pdf.setFillColor(colors.black)
    pdf.setFont('Helvetica', 9)
    pdf.drawString(40, 650, 'Left column text')
    pdf.drawString(320, 650, 'Right column text')
    pdf.drawString(40, 620, 'Normal words with spaces')
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(40, 600, 'Italic words')
    # A nested Form XObject containing both text and graphics. Its text must
    # stay editable and must not leak into the raster graphics layer.
    pdf.beginForm('nested')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(40, 550, 'Nested form text')
    pdf.setFillColor(colors.red)
    pdf.rect(40, 520, 20, 10, fill=1, stroke=0)
    pdf.endForm()
    pdf.doForm('nested')
    pdf.showPage()
    pdf.setPageSize((850, 595))
    pdf.setFont('Times-Roman', 11)
    pdf.drawString(40, 540, 'Landscape second page')
    table = Table([['Merged heading', ''], ['0000123', 'A value']], colWidths=[120, 180], rowHeights=[24, 24])
    table.setStyle(TableStyle([('SPAN', (0, 0), (1, 0)),
                               ('GRID', (0, 0), (-1, -1), .5, colors.black),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('FONTSIZE', (0, 0), (-1, -1), 8)]))
    table.wrapOn(pdf, 300, 48)
    table.drawOn(pdf, 40, 430)
    pdf.save()
    logo.close()
    return path


def test_styles_spaces_columns_and_page_dimensions_survive(layout_pdf):
    ir = extract_digital(layout_pdf)
    reopened = Document(BytesIO(export_docx(ir)))
    texts = [p.text for p in reopened.paragraphs]
    for expected in ('A styled heading', 'Left column text', 'Right column text',
                     'Normal words with spaces', 'Italic words', 'Nested form text', 'Landscape second page'):
        assert texts.count(expected) == 1
    heading = next(p for p in reopened.paragraphs if p.text == 'A styled heading')
    assert heading.runs[0].bold
    assert heading.runs[0].font.size.pt == 13
    assert str(heading.runs[0].font.color.rgb) == '0000FF'
    assert next(p for p in reopened.paragraphs if p.text == 'Italic words').runs[0].italic
    left = next(p for p in reopened.paragraphs if p.text == 'Left column text')
    right = next(p for p in reopened.paragraphs if p.text == 'Right column text')
    assert int(left._p.pPr.find(qn('w:framePr')).get(qn('w:x'))) < int(right._p.pPr.find(qn('w:framePr')).get(qn('w:x')))
    assert [(s.page_width.pt, s.page_height.pt) for s in reopened.sections] == [(595, 850), (850, 595)]
    assert 'Conversion warnings' not in texts
    assert all(w.code != 'LAYOUT_ASSETS_UNAVAILABLE' for p in ir.pages for w in p.warnings)


def test_assets_are_embedded_and_graphics_exclude_nested_text(layout_pdf):
    before = sha256(layout_pdf.read_bytes()).hexdigest()
    ir = extract_digital(layout_pdf)
    assert sha256(layout_pdf.read_bytes()).hexdigest() == before
    assert any(e.engine_name == 'pypdfium2' and e.engine_version for e in ir.engines_used)
    graphics = next(i for i in ir.pages[0].images if i.kind == 'graphics')
    raster = Image.open(BytesIO(base64.b64decode(graphics.data_uri.split(',')[1])))
    # The nested text is at y~292; this non-graphic region must be transparent.
    x = round((45 - graphics.location.x0) / graphics.location.width * raster.width)
    y = round((294 - graphics.location.y0) / graphics.location.height * raster.height)
    assert raster.convert('RGBA').getpixel((x, y))[3] == 0
    assert any(i.kind == 'embedded' for i in ir.pages[0].images)
    # Round-trip the IR and remove access to the source: Word remains portable.
    restored = DocumentIR.model_validate_json(ir.model_dump_json())
    layout_pdf.unlink()
    data = export_docx(restored)
    with ZipFile(BytesIO(data)) as archive:
        assert len([n for n in archive.namelist() if n.startswith('word/media/')]) >= 2
        xml = archive.read('word/document.xml').decode()
        assert 'behindDoc="1"' in xml
        assert 'wp:positionH relativeFrom="page"' in xml
        assert 'r:link=' not in xml
    word = Document(BytesIO(data))
    word.paragraphs[1].add_run(' An edit')
    saved = BytesIO()
    word.save(saved)
    assert Document(BytesIO(saved.getvalue())).paragraphs[1].text.endswith(' An edit')


def test_merged_tables_remain_editable_with_measured_widths(layout_pdf):
    ir = extract_digital(layout_pdf)
    data = export_docx(ir)
    word = Document(BytesIO(data))
    assert len(word.tables) == 1
    table = word.tables[0]
    assert table.cell(0, 0).text == 'Merged heading'
    assert table.cell(0, 0)._tc is table.cell(0, 1)._tc
    assert table.cell(1, 0).text == '0000123'
    assert [column.width.pt for column in table.columns] == [120, 180]
    table.cell(1, 1).text = 'Edited value'
    saved = BytesIO()
    word.save(saved)
    assert Document(BytesIO(saved.getvalue())).tables[0].cell(1, 1).text == 'Edited value'


def test_image_budget_failure_preserves_text_and_reports_it(layout_pdf, monkeypatch):
    from packages.converters import layout
    monkeypatch.setattr(layout, 'MAX_DOCUMENT_ASSET_BYTES', 1)
    ir = extract_digital(layout_pdf)
    assert 'Normal words with spaces' in ir.get_all_text()
    assert any(w.code == 'LAYOUT_ASSETS_UNAVAILABLE' for p in ir.pages for w in p.warnings)
    assert not ir.get_all_images()
    assert Document(BytesIO(export_docx(ir)))


def test_without_word_avoids_rendering_and_reports_omitted_images(layout_pdf, monkeypatch):
    from packages.converters.layout import LayoutAssets
    def unexpected(*args):
        pytest.fail('Image rendering must not run without Word')
    monkeypatch.setattr(LayoutAssets, 'extract', unexpected)
    ir = extract_digital(layout_pdf, preserve_layout=False)
    assert not ir.get_all_images()
    assert any(w.code == 'IMAGES_NOT_EXTRACTED' for w in ir.pages[0].warnings)


@pytest.mark.parametrize('ocr', [False, True])
def test_scan_background_does_not_duplicate_ocr_text(tmp_path, monkeypatch, ocr):
    path = tmp_path / 'scan.pdf'
    image = Image.new('RGB', (600, 800), 'white')
    pdf = canvas.Canvas(str(path), pagesize=(300, 400))
    pdf.drawImage(ImageReader(image), 0, 0, width=300, height=400)
    pdf.save()
    from packages.converters import ocr as ocr_module
    monkeypatch.setattr(ocr_module, 'ocr_page', lambda *_: ('Recognized sample', .95))
    ir = extract_digital(path, ocr=ocr)
    if ocr:
        assert not ir.pages[0].images
        assert ir.pages[0].blocks[0].content == 'Recognized sample'
        assert any(w.code == 'OCR_LAYOUT_APPROXIMATE' for w in ir.pages[0].warnings)
        word = Document(BytesIO(export_docx(ir)))
        assert sum(p.text == 'Recognized sample' for p in word.paragraphs) == 1
    else:
        assert not ir.pages[0].blocks
        assert ir.pages[0].images[0].kind == 'scanned_page'
        assert any(w.code == 'OCR_REQUIRED' for w in ir.pages[0].warnings)
        assert export_docx(ir).startswith(b'PK')


def test_legacy_ir_without_layout_fields_can_still_export(layout_pdf):
    legacy = extract_digital(layout_pdf, preserve_layout=False).model_dump()
    legacy['schema_version'] = '1.0.0'
    for page in legacy['pages']:
        for block in page['blocks']:
            block.pop('runs')
        for table in page['tables']:
            for key in ('column_widths', 'row_heights', 'text_lines'):
                table.pop(key)
            for cell in table['cells']:
                for key in ('runs', 'padding_left', 'padding_top'):
                    cell.pop(key)
    restored = DocumentIR.model_validate(legacy)
    assert restored.schema_version == '1.0.0'
    assert DocumentIR.model_fields['schema_version'].default == '1.1.0'
    assert 'Normal words with spaces' in '\n'.join(p.text for p in Document(BytesIO(export_docx(restored))).paragraphs)


def test_selected_page_and_optional_warnings_annex(layout_pdf):
    ir = extract_digital(layout_pdf, page_numbers=[2])
    assert [p.page_number for p in ir.pages] == [2]
    word = Document(BytesIO(export_docx(ir, include_warnings=True)))
    assert any(p.text == 'Conversion warnings' for p in word.paragraphs)
    assert not any(p.text == 'Left column text' for p in word.paragraphs)


def test_remote_image_references_are_not_loaded(layout_pdf):
    ir = extract_digital(layout_pdf)
    ir.pages[0].images[0].data_uri = 'https://example.invalid/image.png'
    with pytest.raises(ValueError, match='self-contained'):
        export_docx(ir)


def test_repeated_form_images_survive_on_each_page(tmp_path):
    path = tmp_path / 'repeated-form.pdf'
    logo = Image.new('RGB', (80, 30), 'navy')
    pdf = canvas.Canvas(str(path), pagesize=(300, 400))
    pdf.beginForm('shared-logo')
    pdf.drawImage(ImageReader(logo), 30, 340, width=80, height=30)
    pdf.setFont('Helvetica', 9)
    pdf.drawString(30, 320, 'Shared heading')
    pdf.endForm()
    for _ in range(2):
        pdf.doForm('shared-logo')
        pdf.showPage()
    pdf.save()
    ir = extract_digital(path)
    assert len(ir.pages) == 2
    assets = [next(i for i in p.images if i.kind == 'embedded') for p in ir.pages]
    for asset in assets:
        with Image.open(BytesIO(base64.b64decode(asset.data_uri.split(',')[1]))) as raster:
            assert raster.getpixel((raster.width // 2, raster.height // 2))[3] == 255
    assert assets[0].data_uri == assets[1].data_uri
    assert not any(w.code == 'LAYOUT_ASSETS_UNAVAILABLE' for p in ir.pages for w in p.warnings)
