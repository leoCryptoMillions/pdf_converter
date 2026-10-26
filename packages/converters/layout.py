"""Bounded, local Word layout extraction. See ADR 0005.

PDFium rasterizes only the non-text layer. Text is removed from a private
in-memory PDF before rendering, including text inside Form XObjects. No
source file is modified and no page screenshot substitutes editable text.
"""
from __future__ import annotations

import base64
from io import BytesIO
import math
import re
from threading import RLock

import pdfplumber

from packages.document_ir.models import ContentWarning, Image, PositionedText, Rectangle, TextRun

PDFIUM_LOCK = RLock()  # PDFium is not thread-safe, even across documents.
MAX_RENDER_PIXELS = 8_000_000
MAX_ASSET_BYTES = 12 * 1024 * 1024
MAX_DOCUMENT_ASSET_BYTES = 48 * 1024 * 1024
MAX_IMAGES_PER_PAGE = 100


def color_hex(value) -> str | None:
    if value is None or isinstance(value, str):
        return None
    values = [value] if isinstance(value, (int, float)) else list(value)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        return None
    if len(values) == 1:
        rgb = values * 3
    elif len(values) == 3:
        rgb = values
    elif len(values) == 4:
        c, m, y, k = values
        rgb = [(1 - v) * (1 - k) for v in (c, m, y)]
    else:
        return None
    return ''.join(f'{round(max(0, min(1, v)) * 255):02X}' for v in rgb)


def font_style(char: dict) -> dict:
    name = re.sub(r'^[A-Z]{6}\+', '', char.get('fontname') or '')
    return dict(font_name=name or None, font_size=float(char.get('size') or 10),
                bold=bool(re.search(r'bold|black|heavy|demi', name, re.I)),
                italic=bool(re.search(r'italic|oblique', name, re.I)),
                color=color_hex(char.get('non_stroking_color')))


def styled_runs(chars: list[dict], expected: str) -> list[TextRun]:
    runs: list[TextRun] = []
    last = None
    for char in sorted(chars, key=lambda c: c['x0']):
        style = font_style(char)
        value = char['text']
        if last and char['x0'] - last['x1'] > 3 and not value.startswith(' '):
            value = ' ' + value
        if runs and all(getattr(runs[-1], key) == val for key, val in style.items()):
            runs[-1].content += value
        else:
            runs.append(TextRun(content=value, **style))
        last = char
    # Ligatures, RTL and unusual positioning: preserve the extractor's content
    # rather than silently changing it while reconstructing styles.
    if ''.join(r.content for r in runs).split() != expected.split():
        return [TextRun(content=expected, **(font_style(chars[0]) if chars else {}))]
    return runs


def positioned_lines(raw) -> list[PositionedText]:
    result = []
    for line in raw.extract_text_lines(return_chars=True):
        segments: list[list[dict]] = [[]]
        # extract_text_lines returns word characters, omitting explicit PDF
        # space glyphs. Reattach them before rebuilding styled line segments.
        spaces = [c for c in raw.chars if c['text'].isspace() and
                  line['x0'] <= (c['x0'] + c['x1']) / 2 <= line['x1'] and
                  line['top'] <= (c['top'] + c['bottom']) / 2 <= line['bottom']]
        for char in sorted([*line['chars'], *spaces], key=lambda c: c['x0']):
            previous = segments[-1][-1] if segments[-1] else None
            if previous and char['x0'] - previous['x1'] > max(12, char['size'] * 1.5):
                segments.append([])
            segments[-1].append(char)
        for chars in segments:
            text = (pdfplumber.utils.extract_text(chars, layout=False) or '').strip()
            if not text:
                continue
            result.append(PositionedText(content=text, runs=styled_runs(chars, text),
                location=Rectangle(x0=min(c['x0'] for c in chars) - raw.bbox[0],
                                   y0=min(c['top'] for c in chars) - raw.bbox[1],
                                   x1=max(c['x1'] for c in chars) - raw.bbox[0],
                                   y1=max(c['bottom'] for c in chars) - raw.bbox[1])))
    return result


def inside(location: Rectangle, box: Rectangle) -> bool:
    return (box.x0 <= (location.x0 + location.x1) / 2 <= box.x1 and
            box.y0 <= (location.y0 + location.y1) / 2 <= box.y1)


def cell_runs(lines: list[PositionedText], content: str) -> list[TextRun]:
    runs = []
    for index, line in enumerate(sorted(lines, key=lambda b: (b.location.y0, b.location.x0))):
        if index:
            runs.append(TextRun(content='\n'))
        runs.extend(r.model_copy(deep=True) for r in line.runs)
    if ''.join(r.content for r in runs).split() != content.split():
        return [TextRun(content=content, **(
            lines[0].runs[0].model_dump(exclude={'content'}) if lines and lines[0].runs else {}))]
    return runs


def _issue(page, code: str, message: str):
    page.warnings.append(ContentWarning(level='warning', code=code, message=message,
                                        page_number=page.page_number))


class LayoutAssets:
    """Private PDFium documents and a shared per-conversion asset budget."""
    def __init__(self, source):
        self.source = source
        self.pdf = None
        self.bytes_used = 0
        self.engine_version = None
        self.pdfium_version = None

    def close(self):
        with PDFIUM_LOCK:
            if self.pdf is not None:
                self.pdf.close()
                self.pdf = None

    def extract(self, raw, page):
        if not (raw.images or raw.curves or raw.lines or raw.rects):
            return
        if not raw.extract_text() and page.blocks:
            _issue(page, 'OCR_LAYOUT_APPROXIMATE',
                   'OCR text has no validated geometry; the scanned background is omitted to avoid duplicate text.')
            return
        # A scan without OCR is explicitly preserved as an image; OCR_REQUIRED
        # remains visible and no editable-text claim is made for that page.
        with PDFIUM_LOCK:
            try:
                self._extract(raw, page)
            except Exception as exc:
                _issue(page, 'LAYOUT_ASSETS_UNAVAILABLE',
                       f'Images/graphics could not be preserved ({type(exc).__name__}); compare with the PDF.')

    def _extract(self, raw, page):
        import pypdfium2 as pdfium
        import pypdfium2.raw as pdfium_c

        self.engine_version = str(pdfium.PYPDFIUM_INFO.version)
        self.pdfium_version = str(pdfium.PDFIUM_INFO.version)

        if len(raw.images) > MAX_IMAGES_PER_PAGE:
            raise ValueError('Page image count exceeds layout limit')
        if self.bytes_used >= MAX_DOCUMENT_ASSET_BYTES:
            raise ValueError('Document image budget exceeded')
        if self.pdf is None:
            self.pdf = pdfium.PdfDocument(self.source)
        pdf_page = self.pdf[page.page_number - 1]
        try:
            width, height = pdf_page.get_size()
            if abs(width - page.width) > 1 or abs(height - page.height) > 1:
                raise ValueError('PDF engines disagree on page geometry')
            if any(obj.type == pdfium_c.FPDF_PAGEOBJ_FORM and obj.level >= 14
                   for obj in pdf_page.get_objects()):
                raise ValueError('Form nesting exceeds safe text-removal depth')
            # Descend through all supported nested forms. Fail visibly if any
            # text remains; a text-bearing background would duplicate content.
            for obj in list(pdf_page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_TEXT])):
                pdf_page.remove_obj(obj)
                obj.close()
            if any(pdf_page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_TEXT])):
                raise ValueError('Text layer removal incomplete')
            pdf_page.gen_content()
            scale = min(2.5, math.sqrt(MAX_RENDER_PIXELS / (width * height)))

            def render():
                bitmap = pdf_page.render(scale=scale, fill_color=(0, 0, 0, 0),
                                         may_draw_forms=False, draw_annots=False)
                try:
                    return bitmap.to_pil().copy()
                finally:
                    bitmap.close()

            raster = render()
            try:
                for index, image in enumerate(raw.images):
                    box = (max(0, image['x0'] - raw.bbox[0]), max(0, image['top'] - raw.bbox[1]),
                           min(width, image['x1'] - raw.bbox[0]), min(height, image['bottom'] - raw.bbox[1]))
                    if box[2] <= box[0] or box[3] <= box[1]:
                        continue
                    pixel_box = (math.floor(box[0] * scale), math.floor(box[1] * scale),
                                 min(raster.width, math.ceil(box[2] * scale)),
                                 min(raster.height, math.ceil(box[3] * scale)))
                    crop = raster.crop(pixel_box)
                    try:
                        # Snap the placement to the actual crop pixel boundary.
                        self._store(page, crop, tuple(v / scale for v in pixel_box),
                                    'embedded' if raw.extract_text() else 'scanned_page', index)
                    finally:
                        crop.close()
            finally:
                raster.close()
            for obj in list(pdf_page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE])):
                pdf_page.remove_obj(obj)
                obj.close()
            pdf_page.gen_content()
            graphics = render()
            try:
                bounds = graphics.getbbox()
                if bounds:
                    crop = graphics.crop(bounds)
                    try:
                        self._store(page, crop, tuple(v / scale for v in bounds), 'graphics', 0)
                    finally:
                        crop.close()
            finally:
                graphics.close()
        finally:
            pdf_page.close()
            # Shared Form resources must start intact on the next page. Never
            # carry destructive object removal across pages of the private PDF.
            self.pdf.close()
            self.pdf = None

    def _store(self, page, raster, box, kind, index):
        buffer = BytesIO()
        raster.save(buffer, format='PNG')  # Fresh PNG, no PDF streams or external references.
        data = buffer.getvalue()
        if len(data) > MAX_ASSET_BYTES or self.bytes_used + len(data) > MAX_DOCUMENT_ASSET_BYTES:
            raise ValueError('Image budget exceeded')
        self.bytes_used += len(data)
        page.images.append(Image(id=f'p{page.page_number}_{kind}_{index}',
            page_number=page.page_number, location=Rectangle(x0=box[0], y0=box[1], x1=box[2], y1=box[3]),
            format='png', width=raster.width, height=raster.height,
            dpi=round(raster.width / (box[2] - box[0]) * 72), kind=kind,
            data_uri='data:image/png;base64,' + base64.b64encode(data).decode('ascii')))
