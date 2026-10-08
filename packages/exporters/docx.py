"""F0 editable paragraphs and tables; images/layout are explicitly out of scope."""
from __future__ import annotations

from io import BytesIO

from packages.document_ir.models import DocumentIR, Table


def export_docx(document: DocumentIR) -> bytes:
    from docx import Document

    output = Document()
    output.core_properties.comments = "F0 prototype; source SHA256: " + document.source_hash
    for index, page in enumerate(document.pages):
        if index:
            output.add_page_break()
        for block in sorted([*page.blocks, *page.tables], key=lambda b: (b.location.y0, b.location.x0)):
            if isinstance(block, Table):
                table = output.add_table(rows=block.rows, cols=block.columns)
                table.style = "Table Grid"
                for cell in block.cells:
                    table.cell(cell.row_index, cell.col_index).text = cell.content
            else:
                output.add_paragraph(block.content)
    output.add_page_break()
    output.add_heading("Conversion warnings", level=1)
    output.add_paragraph("F0 prototype: editable text and tables; approximate reading order. Images, signatures and original layout are not reproduced.")
    for issue in document.warnings + [w for p in document.pages for w in p.warnings]:
        output.add_paragraph(f"Page {issue.page_number}: {issue.code} — {issue.message}")
    buffer = BytesIO()
    output.save(buffer)
    return buffer.getvalue()
