#!/usr/bin/env python3
"""Generate a synthetic INE-style ID card PDF for the F0 corpus (P01).

All data is fictional. This exists to provide a government-ID-shaped
test case for OCR/layout extraction WITHOUT using any real person's
identity document (a real INE scan was deliberately excluded from this
corpus - see docs/AVANCE.md). The photo is a drawn placeholder, not a
real photograph.

Usage:
    python benchmarks/generate_synthetic_id_card.py

Output: benchmarks/corpus/files/synthetic_ine_mockup.pdf
Rendered as an image-only PDF (no text layer), matching how a real
scanned ID would look, so it is a meaningful scanned_clean test case.
"""
from __future__ import annotations

import io
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, black, white, lightgrey, grey

import pypdfium2 as pdfium
from PIL import Image

CORPUS_FILES_DIR = Path(__file__).resolve().parent / "corpus" / "files"

FAKE_DATA = {
    "nombre_linea1": "PRUEBA SOLIS",
    "nombre_linea2": "JUAN FICTICIO",
    "domicilio": ["CALLE FICTICIA 123", "COL EJEMPLO DE PRUEBA", "CIUDAD FICTICIA, CF"],
    "fecha_nacimiento": "01/01/1990",
    "sexo": "H",
    "clave_elector": "PRSLJN90010100H000",
    "curp": "PRSJ900101HCFXXX00",
    "estado": "00",
    "municipio": "000",
    "seccion": "0000",
    "localidad": "0000",
    "emision": "2020",
    "vigencia": "2030",
    "ano_registro": "2020 00",
}

WATERMARK_TEXT = "DOCUMENTO SINTÉTICO - NO VÁLIDO - SOLO PARA PRUEBAS"


def _draw_photo_placeholder(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(lightgrey)
    c.rect(x, y, w, h, fill=1, stroke=1)
    c.setFillColor(grey)
    c.circle(x + w / 2, y + h * 0.62, w * 0.22, fill=1, stroke=0)
    c.ellipse(x + w * 0.15, y, x + w * 0.85, y + h * 0.45, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + w / 2, y - 8, "FOTO DE PRUEBA")


def _draw_front(c: canvas.Canvas, origin_x: float, origin_y: float) -> None:
    card_w, card_h = 260, 160
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.roundRect(origin_x, origin_y, card_w, card_h, 6, fill=1, stroke=1)

    c.setFillColor(HexColor("#7a1f2b"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(origin_x + 55, origin_y + card_h - 14, "INSTITUTO NACIONAL ELECTORAL")
    c.setFont("Helvetica", 7)
    c.drawString(origin_x + 55, origin_y + card_h - 23, "CREDENCIAL PARA VOTAR (SINTÉTICA)")

    _draw_photo_placeholder(c, origin_x + 8, origin_y + 30, 55, 95)

    text_x = origin_x + 72
    text_y = origin_y + card_h - 35
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 6)
    c.drawString(text_x, text_y, "NOMBRE")
    c.setFont("Helvetica", 7)
    c.drawString(text_x, text_y - 9, FAKE_DATA["nombre_linea1"])
    c.drawString(text_x, text_y - 18, FAKE_DATA["nombre_linea2"])

    c.setFont("Helvetica-Bold", 6)
    c.drawString(text_x, text_y - 30, "DOMICILIO")
    c.setFont("Helvetica", 6.5)
    for i, line in enumerate(FAKE_DATA["domicilio"]):
        c.drawString(text_x, text_y - 39 - (i * 8), line)

    c.setFont("Helvetica-Bold", 6)
    c.drawString(origin_x + 190, origin_y + card_h - 35, "FECHA DE NACIMIENTO")
    c.setFont("Helvetica", 7)
    c.drawString(origin_x + 190, origin_y + card_h - 44, FAKE_DATA["fecha_nacimiento"])
    c.setFont("Helvetica-Bold", 6)
    c.drawString(origin_x + 190, origin_y + card_h - 55, "SEXO")
    c.setFont("Helvetica", 7)
    c.drawString(origin_x + 190, origin_y + card_h - 64, FAKE_DATA["sexo"])

    small_y = origin_y + 20
    c.setFont("Helvetica-Bold", 5.5)
    c.drawString(text_x, small_y, "CLAVE DE ELECTOR")
    c.setFont("Helvetica", 6.5)
    c.drawString(text_x, small_y - 8, FAKE_DATA["clave_elector"])

    c.setFont("Helvetica-Bold", 5.5)
    c.drawString(text_x + 120, small_y, "CURP")
    c.setFont("Helvetica", 6.5)
    c.drawString(text_x + 120, small_y - 8, FAKE_DATA["curp"])

    fields = [
        ("ESTADO", FAKE_DATA["estado"], 0),
        ("MUNICIPIO", FAKE_DATA["municipio"], 45),
        ("SECCIÓN", FAKE_DATA["seccion"], 110),
    ]
    for label, value, dx in fields:
        c.setFont("Helvetica-Bold", 5.5)
        c.drawString(origin_x + 8 + dx, origin_y + 8, label)
        c.setFont("Helvetica", 6.5)
        c.drawString(origin_x + 8 + dx, origin_y + 1, value)

    c.setFont("Helvetica-Bold", 5.5)
    c.drawString(origin_x + 190, origin_y + 8, "VIGENCIA")
    c.setFont("Helvetica", 6.5)
    c.drawString(origin_x + 190, origin_y + 1, FAKE_DATA["vigencia"])


def _draw_back(c: canvas.Canvas, origin_x: float, origin_y: float) -> None:
    card_w, card_h = 260, 160
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.roundRect(origin_x, origin_y, card_w, card_h, 6, fill=1, stroke=1)

    # Fake barcode (bars only, not a scannable real barcode)
    import random

    rnd = random.Random(42)
    bar_x = origin_x + 10
    for _ in range(80):
        bar_w = rnd.choice([1, 1, 2])
        if rnd.random() > 0.4:
            c.setFillColor(black)
            c.rect(bar_x, origin_y + card_h - 35, bar_w, 25, fill=1, stroke=0)
        bar_x += bar_w + 1
        if bar_x > origin_x + 180:
            break

    # Fake QR placeholder
    c.setFillColor(lightgrey)
    c.rect(origin_x + 200, origin_y + card_h - 45, 45, 35, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica", 5)
    c.drawCentredString(origin_x + 222, origin_y + card_h - 25, "QR DE")
    c.drawCentredString(origin_x + 222, origin_y + card_h - 33, "PRUEBA")

    # Fake signature + fingerprint placeholders
    c.setFont("Helvetica", 14)
    c.setFillColor(grey)
    c.drawString(origin_x + 15, origin_y + card_h - 75, "firma de prueba")
    c.setFillColor(lightgrey)
    c.rect(origin_x + 150, origin_y + card_h - 90, 40, 30, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica", 5)
    c.drawCentredString(origin_x + 170, origin_y + card_h - 83, "HUELLA DE")
    c.drawCentredString(origin_x + 170, origin_y + card_h - 91, "PRUEBA")

    # Fake MRZ lines
    mrz_lines = [
        "IDMEX0000000000<<00000000000000",
        "9001010H30010100MEX<<00000000<0",
        FAKE_DATA["nombre_linea1"] + "<<" + FAKE_DATA["nombre_linea2"] + "<<<",
    ]
    c.setFont("Courier", 8)
    c.setFillColor(black)
    for i, line in enumerate(mrz_lines):
        c.drawString(origin_x + 10, origin_y + 30 - (i * 10), line)


def _add_watermark(c: canvas.Canvas, page_w: float, page_h: float) -> None:
    c.saveState()
    c.setFillColor(HexColor("#ff0000"))
    c.setFont("Helvetica-Bold", 14)
    c.translate(page_w / 2, page_h / 2)
    c.rotate(30)
    c.setFillAlpha(0.35)
    c.drawCentredString(0, 150, WATERMARK_TEXT)
    c.drawCentredString(0, -150, WATERMARK_TEXT)
    c.restoreState()


def build_vector_pdf(path: Path) -> None:
    page_w, page_h = letter
    c = canvas.Canvas(str(path), pagesize=letter)
    _draw_front(c, (page_w - 260) / 2, page_h - 260)
    _draw_back(c, (page_w - 260) / 2, page_h - 540)
    _add_watermark(c, page_w, page_h)
    c.showPage()
    c.save()


def rasterize_to_image_only_pdf(vector_pdf: Path, out_path: Path) -> None:
    """Strip the text layer by rendering to an image and re-embedding it,
    so the result behaves like a real scan for OCR benchmark purposes."""
    pdf = pdfium.PdfDocument(str(vector_pdf))
    page = pdf[0]
    bitmap = page.render(scale=2.0)
    pil_image = bitmap.to_pil()

    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    buf.seek(0)

    page_w, page_h = letter
    c = canvas.Canvas(str(out_path), pagesize=letter)
    c.drawImage(
        __import__("reportlab.lib.utils", fromlist=["ImageReader"]).ImageReader(buf),
        0,
        0,
        width=page_w,
        height=page_h,
        preserveAspectRatio=True,
        anchor="c",
    )
    c.showPage()
    c.save()


def main() -> None:
    CORPUS_FILES_DIR.mkdir(parents=True, exist_ok=True)
    vector_path = CORPUS_FILES_DIR / "_synthetic_ine_mockup_vector_tmp.pdf"
    final_path = CORPUS_FILES_DIR / "synthetic_ine_mockup.pdf"

    build_vector_pdf(vector_path)
    rasterize_to_image_only_pdf(vector_path, final_path)
    vector_path.unlink()

    print(f"Generado: {final_path.name}")
    print("Todos los datos son ficticios. La foto es un placeholder dibujado, no una fotografia real.")


if __name__ == "__main__":
    main()
