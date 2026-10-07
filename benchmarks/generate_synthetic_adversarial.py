#!/usr/bin/env python3
"""Generate synthetic adversarial PDFs for the F0 corpus (P01).

Creates a small synthetic invoice-like PDF (fake data only - no real
customer/financial information) and derives the two adversarial samples
that real documents in the corpus don't cover yet:
  - adversarial_encrypted: the same content, password-protected
  - adversarial_corrupt: the same content, truncated mid-file

Usage:
    python benchmarks/generate_synthetic_adversarial.py

Outputs go to benchmarks/corpus/files/ (gitignored) and are already
reflected in corpus_manifest.csv.
"""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

CORPUS_FILES_DIR = Path(__file__).resolve().parent / "corpus" / "files"
ENCRYPTED_PASSWORD = "f0-test-1234"

FAKE_TABLE_DATA = [
    ["Concepto", "Cantidad", "Precio Unitario", "Importe"],
    ["Servicio de prueba A", "2", "$100.00", "$200.00"],
    ["Servicio de prueba B", "1", "$350.50", "$350.50"],
    ["Licencia de software (demo)", "5", "$40.00", "$200.00"],
    ["Total", "", "", "$750.50"],
]


def build_base_pdf(path: Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    table = Table(FAKE_TABLE_DATA, colWidths=[7 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, -1), (-1, -1), colors.whitesmoke),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story = [
        Paragraph("FACTURA DE PRUEBA SINTÉTICA (datos ficticios)", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "Documento generado automáticamente para probar el manejo de PDFs "
            "cifrados y corruptos (categorías adversarial_encrypted / "
            "adversarial_corrupt). No contiene datos reales.",
            styles["Normal"],
        ),
        Spacer(1, 20),
        table,
    ]
    doc.build(story)


def make_encrypted(src: Path, dst: Path, password: str) -> None:
    reader = PdfReader(str(src))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with dst.open("wb") as f:
        writer.write(f)


def make_corrupt(src: Path, dst: Path, truncate_fraction: float = 0.6) -> None:
    data = src.read_bytes()
    cutoff = int(len(data) * truncate_fraction)
    dst.write_bytes(data[:cutoff])


def main() -> None:
    CORPUS_FILES_DIR.mkdir(parents=True, exist_ok=True)
    base_path = CORPUS_FILES_DIR / "synthetic_base_invoice.pdf"
    encrypted_path = CORPUS_FILES_DIR / "synthetic_adversarial_encrypted_001.pdf"
    corrupt_path = CORPUS_FILES_DIR / "synthetic_adversarial_corrupt_001.pdf"

    build_base_pdf(base_path)
    make_encrypted(base_path, encrypted_path, ENCRYPTED_PASSWORD)
    make_corrupt(base_path, corrupt_path)

    print(f"Base (también sirve como digital_simple_table sintético): {base_path.name}")
    print(f"Cifrado (password: {ENCRYPTED_PASSWORD}): {encrypted_path.name}")
    print(f"Corrupto (truncado): {corrupt_path.name}")
    print("\nAgrega estas filas a corpus_manifest.csv (ya incluidas si usaste la versión actualizada).")


if __name__ == "__main__":
    main()
