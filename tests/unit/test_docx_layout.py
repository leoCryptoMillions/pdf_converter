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


@pytest.mark.mvp
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


@pytest.mark.mvp
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


@pytest.mark.mvp
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


@pytest.mark.mvp
def test_image_budget_failure_preserves_text_and_reports_it(layout_pdf, monkeypatch):
    from packages.converters import layout
    monkeypatch.setattr(layout, 'MAX_DOCUMENT_ASSET_BYTES', 1)
    ir = extract_digital(layout_pdf)
    assert 'Normal words with spaces' in ir.get_all_text()
    assert any(w.code == 'LAYOUT_ASSETS_UNAVAILABLE' for p in ir.pages for w in p.warnings)
    assert not ir.get_all_images()
    assert Document(BytesIO(export_docx(ir)))


@pytest.mark.mvp
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


@pytest.mark.mvp
def test_multi_page_scans_use_jpeg_to_fit_the_shared_image_budget(tmp_path, monkeypatch):
    # Real-world bug (2026-10-27, a real 32-page scanned newspaper with no
    # digital text): every full-page scan was stored as lossless PNG
    # (~6MB each for photographic content) and the shared per-document
    # image budget ran out after ~8 pages, leaving the rest of the document
    # completely blank - no text (it's a scan) and no image (budget
    # exceeded). JPEG for this specific case (a visual fallback already
    # flagged OCR_REQUIRED, never authoritative text) is a quarter of the
    # size here, same as the real document, so far more pages fit.
    import random
    from packages.converters import layout as layout_module

    photo = Image.new('RGB', (300, 300))
    random.seed(0)
    pixels = []
    for y in range(300):
        base = (y * 255 // 300, 120, 255 - y * 255 // 300)
        for _ in range(300):
            noise = random.randrange(-20, 20)
            pixels.append(tuple(max(0, min(255, c + noise)) for c in base))
    photo.putdata(pixels)

    path = tmp_path / 'scanned-newspaper.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(300, 300))
    for _ in range(3):
        pdf.drawImage(ImageReader(photo), 0, 0, width=300, height=300)
        pdf.showPage()
    pdf.save()

    # Comfortably above 3x this image's actual rendered JPEG size (~98KB
    # each) but well under even a single rendered PNG of it (~770KB): the
    # old PNG path would have exceeded this budget on page 1; the JPEG path
    # fits all 3 pages, exactly like the real fix.
    monkeypatch.setattr(layout_module, 'MAX_DOCUMENT_ASSET_BYTES', 350_000)

    ir = extract_digital(path)
    assert len(ir.pages) == 3
    assert [p.images[0].format for p in ir.pages if p.images] == ['jpeg'] * 3
    assert not any(w.code == 'LAYOUT_ASSETS_UNAVAILABLE' for p in ir.pages for w in p.warnings)
    word = Document(BytesIO(export_docx(ir)))
    assert len(word.sections) == 3


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


@pytest.mark.mvp
def test_selected_page_and_optional_warnings_annex(layout_pdf):
    ir = extract_digital(layout_pdf, page_numbers=[2])
    assert [p.page_number for p in ir.pages] == [2]
    word = Document(BytesIO(export_docx(ir, include_warnings=True)))
    assert any(p.text == 'Conversion warnings' for p in word.paragraphs)
    assert not any(p.text == 'Left column text' for p in word.paragraphs)


@pytest.mark.mvp
def test_tightly_stacked_lines_do_not_overlap_in_word(tmp_path):
    # A large heading immediately followed by a much closer line than its own
    # font size implies (e.g. a receipt's title sitting right above a folio
    # number) must not force a Word frame taller than the real gap between
    # them, or the heading's text paints over the line below it.
    path = tmp_path / 'tight.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(595, 850))
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawString(40, 760, 'Tight Heading')
    pdf.setFont('Helvetica', 9)
    pdf.drawString(40, 750, 'Immediately below the heading')
    pdf.save()

    ir = extract_digital(path)
    word = Document(BytesIO(export_docx(ir)))

    heading = next(p for p in word.paragraphs if p.text == 'Tight Heading')
    below = next(p for p in word.paragraphs if p.text == 'Immediately below the heading')
    heading_frame = heading._p.pPr.find(qn('w:framePr'))
    below_frame = below._p.pPr.find(qn('w:framePr'))
    heading_top = int(heading_frame.get(qn('w:y')))
    below_top = int(below_frame.get(qn('w:y')))
    heading_height_twips = round(heading.paragraph_format.line_spacing.pt * 20)
    assert heading_top + heading_height_twips <= below_top
    # Confirms the gap-based clamp actually fired, not just a lucky layout:
    # the heading's own font-size-based spacing (20*1.15=23pt) would overlap.
    assert heading.paragraph_format.line_spacing.pt < 23


@pytest.mark.mvp
def test_unrecognized_embedded_font_falls_back_to_a_safe_width_predictable_font(tmp_path):
    # Real-world bug (2026-10-27, user-provided receipt): a PDF embedding a
    # branded font like "Lato-Bold" that isn't Helvetica/Times/Courier was
    # requested from Word by its literal name. Word substituted it with an
    # unknown, wider fallback, wrapping the heading to a second line inside
    # its own single-line frame and overlapping the content right below it.
    # Forcing unrecognized fonts to Arial makes the substitution predictable.
    import reportlab
    from pathlib import Path
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pdfmetrics.registerFont(TTFont('Lato-Bold', str(Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf')))
    path = tmp_path / 'custom-font.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(595, 850))
    pdf.setFont('Lato-Bold', 15)
    pdf.drawString(20, 800, 'Comprobante de operacion')
    pdf.setFont('Helvetica', 12)
    pdf.drawString(20, 782, 'FOLIO-1234567890')
    pdf.save()

    ir = extract_digital(path)
    word = Document(BytesIO(export_docx(ir)))
    heading = next(p for p in word.paragraphs if p.text == 'Comprobante de operacion')
    assert heading.runs[0].font.name == 'Arial'
    assert any(w.code == 'DOCX_FONT_SUBSTITUTED' for p in ir.pages for w in p.warnings)


@pytest.mark.mvp
def test_small_font_words_with_no_space_glyph_stay_separated(tmp_path):
    # Real-world bug (2026-10-27, a SAT "Constancia de Situacion Fiscal"):
    # some PDF generators position each word individually at a small visual
    # gap without an actual space character glyph between them. At small
    # font sizes (8pt here, matching the real document) that gap is well
    # under pdfplumber's flat default x_tolerance=3, so both a table cell's
    # text and a free-flowing paragraph line merge every word together with
    # no spaces - in a table cell ("Sociedadesfinancieras...") and in body
    # text alike.
    path = tmp_path / 'tight-words.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(400, 400))
    font, size, gap = 'Helvetica', 8, 2.2

    def draw_words(y, words):
        x = 40.0
        for word in words:
            pdf.setFont(font, size)
            pdf.drawString(x, y, word)
            x += pdf.stringWidth(word, font, size) + gap

    # A free paragraph line, no table involved.
    draw_words(360, ['Sus', 'datos', 'personales'])

    # A two-row, one-column table (a single-cell box isn't recognized as a
    # table by pdfplumber's default "lines" strategy; a header row is the
    # minimal structure it detects, same grid technique as layout_pdf
    # below). Leave the data cell empty and draw the tight-gap words over it
    # directly, since the flowable's own text layout would insert real
    # space glyphs and not reproduce the bug.
    table = Table([['Actividad'], ['']], colWidths=[250], rowHeights=[20, 20])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), .5, colors.black)]))
    table.wrapOn(pdf, 250, 40)
    table.drawOn(pdf, 40, 280)
    draw_words(286, ['Sociedades', 'financieras', 'de', 'objeto'])
    pdf.save()

    ir = extract_digital(path)
    page = ir.pages[0]
    paragraph_text = next(b.content for b in page.blocks if b.content.startswith('Sus'))
    assert paragraph_text == 'Sus datos personales'
    cell_text = next(c.content for c in page.tables[0].cells if c.row_index == 1)
    assert cell_text == 'Sociedades financieras de objeto'

    word = Document(BytesIO(export_docx(ir)))
    assert any(p.text == 'Sus datos personales' for p in word.paragraphs)
    assert word.tables[0].cell(1, 0).text == 'Sociedades financieras de objeto'


@pytest.mark.mvp
def test_remote_image_references_are_not_loaded(layout_pdf):
    ir = extract_digital(layout_pdf)
    ir.pages[0].images[0].data_uri = 'https://example.invalid/image.png'
    with pytest.raises(ValueError, match='self-contained'):
        export_docx(ir)


@pytest.mark.mvp
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


@pytest.mark.mvp
def test_painted_backgrounds_do_not_become_padding_cells(tmp_path):
    path = tmp_path / 'painted-grid.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(400, 400))
    for row, y in enumerate([230, 200]):
        for column, x in enumerate([40, 190]):
            pdf.setFillColor(colors.lightgrey if row == 0 else colors.whitesmoke)
            pdf.rect(x, y, 150, 30, fill=1, stroke=0)
            pdf.rect(x + 5, y + 5, 140, 20, fill=1, stroke=0)
            for dx, dy, width, height in [(0, 0, 5, 30), (145, 0, 5, 30),
                                           (0, 0, 150, 5), (0, 25, 150, 5)]:
                pdf.rect(x + dx, y + dy, width, height, fill=1, stroke=0)
            pdf.setFillColor(colors.black)
            pdf.setFont('Helvetica-Oblique' if row else 'Helvetica-Bold', 9)
            pdf.drawString(x + 7, y + 11, [['Header one', 'Header two'], ['Value A', 'Value B']][row][column])
    pdf.setFillColor(colors.black)
    for y in [200, 230, 260]:
        pdf.rect(40, y, 300, .5, fill=1, stroke=0)
    for x in [40, 190, 340]:
        pdf.rect(x, 200, .5, 60, fill=1, stroke=0)
    pdf.save()
    ir = extract_digital(path)
    table = ir.pages[0].tables[0]
    assert (table.rows, table.columns) == (2, 2)
    assert [c.content for c in table.cells] == ['Header one', 'Header two', 'Value A', 'Value B']
    assert any(w.code == 'TABLE_DECORATION_FILTERED' for w in ir.pages[0].warnings)
    word = Document(BytesIO(export_docx(ir)))
    assert word.tables[0].cell(1, 1).text == 'Value B'
    assert all(r.italic for r in word.tables[0].cell(1, 1).paragraphs[0].runs if r.text.strip())
    assert (len(word.tables[0].rows), len(word.tables[0].columns)) == (2, 2)


@pytest.mark.mvp
def test_empty_padding_rows_keep_a_small_line_height(tmp_path):
    path = tmp_path / 'small-padding.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(400, 400))
    table = Table([['', ''], ['One', 'Two'], ['', '']], colWidths=[100, 100], rowHeights=[4.5, 20, 4.5])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), .5, colors.black),
                               ('FONTSIZE', (0, 0), (-1, -1), 8)]))
    table.wrapOn(pdf, 200, 29)
    table.drawOn(pdf, 40, 250)
    pdf.save()
    ir = extract_digital(path)
    word = Document(BytesIO(export_docx(ir)))
    assert word.tables[0].cell(1, 1).text == 'Two'
    for index in [0, 2]:
        for cell in word.tables[0].rows[index].cells:
            assert cell.paragraphs[0].paragraph_format.line_spacing.pt <= 4.5


@pytest.mark.mvp
@pytest.mark.parametrize(('ligature', 'expanded'), [('\ufb01', 'fi'), ('\ufb02', 'fl')])
def test_word_ligatures_expand_once_and_repeated_glyphs_survive(tmp_path, ligature, expanded):
    import reportlab
    from pathlib import Path
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from benchmarks.validate_word import word_text

    pdfmetrics.registerFont(TTFont('PilotVera', str(Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf')))
    path = tmp_path / 'ligatures.pdf'
    pdf = canvas.Canvas(str(path), pagesize=(400, 400))
    pdf.setFont('PilotVera', 12)
    for y in (300, 270):
        pdf.drawString(40, y, f'A {ligature} {ligature} B')
    pdf.save()
    ir = extract_digital(path)
    expected = f'A {expanded} {expanded} B'
    assert ir.pages[0].extracted_text.splitlines() == [expected, expected]
    word = Document(BytesIO(export_docx(ir)))
    assert [line for line in word_text(word).splitlines() if line.strip()] == [expected, expected]


@pytest.mark.mvp
def test_truly_blank_page_does_not_request_ocr(tmp_path, monkeypatch):
    path = tmp_path / 'blank.pdf'
    pdf = canvas.Canvas(str(path))
    pdf.showPage()
    pdf.save()
    from packages.converters import ocr as ocr_module
    def unexpected(*args):
        pytest.fail('OCR must not run on a structurally blank page')
    monkeypatch.setattr(ocr_module, 'ocr_page', unexpected)
    ir = extract_digital(path, ocr=True)
    assert ir.pages[0].metadata['blank_page'] is True
    assert any(w.code == 'EMPTY_PAGE' for w in ir.pages[0].warnings)
    assert not any(w.code == 'OCR_REQUIRED' for w in ir.pages[0].warnings)
    assert len(Document(BytesIO(export_docx(ir))).sections) == 1
