"""Link table segments using page geometry; preserve every source row/cell."""
from __future__ import annotations

from packages.document_ir.models import ContentWarning, DocumentIR, Page, Table


def column_edges(table: Table, page: Page) -> list[float] | None:
    edges = []
    for column in range(table.columns):
        cells = [cell for cell in table.cells if cell.col_index == column and cell.original_source]
        if not cells or any(cell.col_span != 1 for cell in cells):
            return None
        left = min(cell.original_source.x0 for cell in cells)
        right = max(cell.original_source.x1 for cell in cells)
        edges.extend([left / page.width, right / page.width])
    return edges


def link_table_continuations(document: DocumentIR) -> None:
    """Conservative candidate links, not a reconstruction of split transactions.

    Requires consecutive source pages, edge-adjacent tables and matching
    column geometry. Always flag review; never remove headers or join rows.
    """
    for previous, current in zip(document.pages, document.pages[1:]):
        if (current.page_number != previous.page_number + 1 or
            current.rotation != previous.rotation or not previous.tables or not current.tables):
            continue
        first = max(previous.tables, key=lambda table: table.location.y1)
        second = min(current.tables, key=lambda table: table.location.y0)
        if (first.columns < 2 or first.columns != second.columns or
            first.location.y1 < previous.height * 0.85 or second.location.y0 > current.height * 0.20):
            continue
        before = column_edges(first, previous)
        after = column_edges(second, current)
        if before is None or after is None or any(abs(a - b) > 0.005 for a, b in zip(before, after)):
            continue
        first.multi_page = second.multi_page = True
        second.continuation_of = first.id
        if not any(w.code == "TABLE_CONTINUATION_CANDIDATE" for w in second.warnings):
            second.warnings.append(ContentWarning(level="warning", code="TABLE_CONTINUATION_CANDIDATE",
                message=f"Column geometry suggests continuation of {first.id}; source segments and all rows are retained.",
                page_number=current.page_number))
        if not any(w.code == "BOUNDARY_ROWS_REQUIRE_REVIEW" for w in second.warnings):
            second.warnings.append(ContentWarning(level="warning", code="BOUNDARY_ROWS_REQUIRE_REVIEW",
                message="Review the last row of the previous segment and first row of this segment; they may be one split row. No automatic concatenation or deduplication.",
                page_number=current.page_number))
