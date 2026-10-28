"""Loss-conscious XLSX export. Original values always remain text."""
from __future__ import annotations

import base64
from decimal import Decimal, InvalidOperation
from io import BytesIO
import math
import re

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.cell.rich_text import CellRichText, TextBlock as _RichRun
from openpyxl.cell.text import InlineFont
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from packages.document_ir.models import DocumentIR, TextRun


def put_text(cell, value: str) -> None:
    if len(value) > 32767 or ILLEGAL_CHARACTERS_RE.search(value):
        raise ValueError("Text cannot be represented losslessly in an XLSX cell")
    if not value:
        # Pre-existing defect found verifying this feature against a real document's
        # blank table cells: openpyxl serializes an explicitly-typed empty string as
        # `<c t="inlineStr"></c>` with no `<is>` child - invalid OOXML. openpyxl's own
        # reader tolerates it, but real Excel refuses to even open the file (Workbooks.Open
        # raises; confirmed against Microsoft Excel via COM automation). A blank source
        # cell has no content to preserve, so leave the cell genuinely empty instead.
        return
    cell.value = value
    cell.data_type = "s"  # Includes =, +, -, @ content; never create a formula.
    cell.number_format = "@"


def _run_style(run: TextRun) -> tuple:
    return (run.font_name, run.font_size, run.bold, run.italic, run.color)


def _argb(color: str | None) -> str | None:
    """Opaque ARGB for openpyxl's Color fields.

    Verified against real openpyxl 3.1.5 behavior: passing a plain 6-digit
    RRGGBB string to InlineFont(color=...) or PatternFill(fgColor=...) does
    NOT get an opaque alpha assumed - openpyxl left-pads it to 8 hex digits
    with "00", i.e. alpha=00 (fully transparent). Both our font colors and
    highlight fills come from document_ir's 6-digit RRGGBB (TextRun.color /
    Cell.fill_color); without this prefix every rich-text color and every
    highlight band would be invisible in real Excel despite being "set".
    """
    return None if color is None else "FF" + color


def _sanitize_runs_for_rich_text(runs: list[TextRun]) -> list[TextRun]:
    """Fold any run whose text is pure whitespace (or empty) into a neighbour.

    A run whose <t> content has nothing but whitespace (e.g. the "\\n" that
    cell_runs()/styled_runs() use to join multiple PDF lines into one cell)
    gets no xml:space="preserve" from openpyxl's writer; real Excel then
    normalizes it away and refuses to even open the file - confirmed via
    Excel COM automation on a real multi-line table cell (a SUBTOTAL/IVA/
    TOTAL block). Re-attaching that text to a styled neighbour preserves
    every character and its order; only which run's style nominally "owns"
    a newline changes, which has no visual effect.
    """
    merged: list[TextRun] = []
    pending = ""
    for run in runs:
        if not run.content.strip():
            pending += run.content
            continue
        content = pending + run.content
        pending = ""
        merged.append(run if content == run.content else run.model_copy(update={"content": content}))
    if pending:
        if merged:
            merged[-1] = merged[-1].model_copy(update={"content": merged[-1].content + pending})
        else:
            merged.append(TextRun(content=pending))
    return merged


def put_rich_text(cell, runs: list[TextRun]) -> None:
    """Write styled runs into one cell, falling back to plain text when safe.

    Mixed per-run styling (e.g. a bold label followed by a plain value on
    the same physical PDF line) cannot be represented by put_text's single
    Font, so a genuinely multi-style line is written as OOXML inline rich
    text instead. Rich/inline text has no formula grammar regardless of
    content, so this remains exactly as formula-safe as put_text, and the
    same length/illegal-character guard runs first, on the joined text.
    """
    joined = "".join(run.content for run in runs)
    if len(joined) > 32767 or ILLEGAL_CHARACTERS_RE.search(joined):
        raise ValueError("Text cannot be represented losslessly in an XLSX cell")
    if len(runs) <= 1 or all(_run_style(run) == _run_style(runs[0]) for run in runs):
        put_text(cell, joined)
        return
    safe_runs = _sanitize_runs_for_rich_text(runs)
    if len(safe_runs) <= 1:
        put_text(cell, joined)
        return
    cell.value = CellRichText(*(
        _RichRun(InlineFont(rFont=run.font_name, sz=run.font_size, b=run.bold,
                             i=run.italic, color=_argb(run.color)), run.content)
        for run in safe_runs))
    cell.data_type = "s"
    cell.number_format = "@"


def _cluster_edges(values: list[float], epsilon: float = 1.0) -> list[float]:
    """Collapse near-duplicate coordinates (float jitter) into shared grid lines."""
    if not values:
        return []
    ordered = sorted(values)
    clusters = [[ordered[0]]]
    for value in ordered[1:]:
        if value - clusters[-1][-1] > epsilon:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return [sum(cluster) / len(cluster) for cluster in clusters]


def _locate(edges: list[float], value: float, tolerance: float = 1.0) -> int:
    """Index of the grid edge nearest value.

    Never raises: by construction, every value passed in was itself one of
    the contributors to the edge set, so its nearest edge is always the
    intended one (tolerance documents the expected float jitter rather than
    gating a lookup failure).
    """
    best_index, best_distance = 0, float("inf")
    for index, edge in enumerate(edges):
        distance = abs(edge - value)
        if distance < best_distance:
            best_index, best_distance = index, distance
    return best_index


def _build_page_grid(page) -> tuple[list[float], list[float]]:
    """Clustered (xs, ys) grid lines covering every table and block on a page.

    Reuses each table's own column_widths/row_heights (including the
    merged-header correction already applied in digital.py), so the page
    grid can never disagree with that table's own Table_N geometry.

    Blocks deliberately contribute only their LEFT edge to xs (never x1):
    collecting a free-text line's own right edge would mint a near-unique
    column per line on any dense paragraph. Collecting only the left edge
    bounds column growth by the number of distinct indentation levels
    actually present on the page.
    """
    xs = {0.0, page.width}
    ys = {0.0, page.height}
    for table in page.tables:
        x = table.location.x0
        xs.add(x)
        for width in table.column_widths:
            x += width
            xs.add(x)
        xs.add(table.location.x1)
        y = table.location.y0
        ys.add(y)
        for height in table.row_heights:
            y += height
            ys.add(y)
        ys.add(table.location.y1)
    for block in page.blocks:
        xs.add(block.location.x0)
        ys.add(block.location.y0)
        ys.add(block.location.y1)
    return _cluster_edges(list(xs)), _cluster_edges(list(ys))


def _ranges_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def _rect_cells(row_start: int, row_end: int, col_start: int, col_end: int):
    """Every grid cell a (possibly merged) placement actually covers.

    A collision check keyed only on the top-left anchor misses the real
    case where a NEW element's own single-cell anchor lands inside a
    PREVIOUS element's multi-row/col merged span (seen on a real quotation:
    a SUBTOTAL label merged across 3 rows, with a sibling cell's anchor
    landing on its second row) - writing to that cell then raises
    AttributeError ("MergedCell ... read-only"), not a safe degrade.
    """
    return {(row, col) for row in range(row_start, row_end) for col in range(col_start, col_end)}


def _block_col_ends(xs: list[float], block_positions, table_positions) -> list[int]:
    """How far right each block's merge may extend before it must stop.

    CORRECTION (found during design re-verification): a block's column span
    must stop at the nearest element sharing its visual row, not always
    reach the page's rightmost column. Two free-text blocks sitting side by
    side on one line (e.g. "SERIE: ..." and "MODELO ..." in a real
    quotation) would otherwise both merge across the full row width and
    their merge_cells ranges would overlap - openpyxl raises on that, a
    real crash risk on exactly the documents this feature targets.

    For each block, the end is the smallest x-grid index, greater than its
    own start, that is the left edge (x0) of some OTHER block or the left
    edge of some table whose own row range overlaps this block's row range
    by at least one shared row band. With no such neighbour, the block is
    alone on its row and may legitimately span to the page's last column.
    """
    ends = []
    for index, (row_start, row_end, col_start) in enumerate(block_positions):
        candidates = [
            other_col for j, (other_start, other_end, other_col) in enumerate(block_positions)
            if j != index and other_col > col_start and _ranges_overlap(row_start, row_end, other_start, other_end)
        ]
        candidates += [
            table_col for (table_row_start, table_row_end, table_col) in table_positions
            if table_col > col_start and _ranges_overlap(row_start, row_end, table_row_start, table_row_end)
        ]
        ends.append(min(candidates) if candidates else len(xs) - 1)
    return ends


def _col_width(xs: list[float], index: int) -> float:
    """Same width formula used for ws.column_dimensions - kept in one place
    so row-height wrap estimation can never disagree with the actual column
    width the text will wrap against."""
    return max(4.0, (xs[index + 1] - xs[index]) / 7.0)


MAX_COL_WIDTH = 40.0


def _widen_for_content(col_widths: list[float], col_start: int, col_end: int, text: str) -> None:
    """Widen a single-column placement's column so its longest word fits on
    one line, instead of Excel hyphenating every word mid-letter.

    A narrow PDF-derived column (e.g. a "CANT." header) is often sized for
    its actual VALUES (short numbers), not its own HEADER word
    ("REFACCIONES") - at the raw PDF-point width, Excel's word-wrap has no
    space boundary to break on inside a too-long word and splits it at any
    character ("REF"/"ACC"/"ION"/"ES" stacked vertically), which is a real
    defect found rendering a real document through actual Excel: visually
    far worse than the source PDF, not "practically identical" to it. Only
    applies to single-column placements (col_span == 1); a merged span
    already has combined room and widening it would need to pick which of
    several columns absorbs the extra space, so it is left alone.
    """
    if col_end - col_start != 1:
        return
    longest = max((len(word) for word in text.split()), default=0)
    if longest > col_widths[col_start]:
        col_widths[col_start] = min(MAX_COL_WIDTH, longest + 1)


def _estimate_wrapped_lines(text: str, avail_chars: float) -> int:
    """How many visual lines `text` needs once Excel wraps it at `avail_chars`.

    Simulates real greedy word-wrap (accumulate words until the next one
    would overflow the line, then start a new line) rather than dividing the
    total character count by the width: a naive division assumes every line
    packs perfectly to the column's edge, but real word-wrap leaves unused
    space whenever a word doesn't quite fit - it reliably UNDER-counts lines
    for long, many-word values (found rendering a real document's long
    legal-entity name through actual Excel: the naive estimate left the row
    one line too short and the last line of text was clipped). This estimate
    is itself still only approximate (Excel's own column-width unit is an
    approximation of character count, per the project's accepted
    width-conversion compromise above), not a pixel-exact layout - but it no
    longer systematically undershoots.
    """
    width = max(1, math.floor(avail_chars))
    lines = 0
    for physical_line in text.split("\n"):
        words = physical_line.split()
        if not words:
            lines += 1
            continue
        current = 0
        wrapped = 1
        for word in words:
            if current and current + 1 + len(word) > width:
                wrapped += 1
                current = len(word)
            else:
                current += (1 if current else 0) + len(word)
        lines += wrapped
    return max(1, lines)


def _required_row_height(text: str, runs: list[TextRun], col_widths: list[float], col_start: int, col_end: int) -> float:
    avail_chars = sum(col_widths[i] for i in range(col_start, col_end))
    font_size = max((r.font_size for r in runs if r.font_size), default=10.0) if runs else 10.0
    # 1.2x line-height is the standard typographic multiplier (also Excel's
    # own default row-height-to-font-size ratio); +2pt padding avoids text
    # sitting flush against the row's lower edge.
    return _estimate_wrapped_lines(text, avail_chars) * font_size * 1.2 + 2


PIXELS_PER_POINT = 96 / 72  # openpyxl sizes images in pixels at 96 DPI; our geometry is in 72-DPI PDF points.


def _embed_page_images(ws, page, xs: list[float], ys: list[float], issues: list) -> None:
    """Embed captured raster images as floating overlays, positioned by their
    PDF location. Never silently drops an image: anything not embedded gets
    an IMAGE_NOT_EMBEDDED warning so the loss is disclosed, per the project's
    core principle of never hiding degradation.

    'graphics' images are a single full-page re-render of all non-text
    vector content (lines, curves, decorative fills) and are deliberately
    NOT embedded here: floating on top of the cell grid, an opaque
    full-page image would cover the very cell text/fills this overlay
    exists to show, trading one disclosed loss for a worse undisclosed one.
    """
    for image in page.images:
        if image.kind == "graphics":
            issues.append(("IMAGE_NOT_EMBEDDED", page.page_number,
                           f"{image.id}: full-page background graphics are not embedded in the page overlay "
                           "(would visually cover cell text); compare with the source PDF."))
            continue
        if not image.data_uri or ";base64," not in image.data_uri:
            issues.append(("IMAGE_NOT_EMBEDDED", page.page_number,
                           f"{image.id}: no embeddable image data was captured; compare with the source PDF."))
            continue
        try:
            _, encoded = image.data_uri.split(";base64,", 1)
            data = base64.b64decode(encoded)
            _validate_image_bytes(data)
            # A fresh, untouched buffer for the actual embedded object: openpyxl
            # reads raw encoded bytes back out of this file-like object at
            # wb.save() time (img.fp.seek(0) + .read()), so it must still be
            # open then - PIL's own Image.load()/verify() always detach and
            # null out .fp once called, which is why validation above uses a
            # separate, throwaway buffer instead of this one.
            pil_image = _open_pil_image(BytesIO(data))
            xl_image = XLImage(pil_image)
            xl_image.width = max(1.0, (image.location.x1 - image.location.x0) * PIXELS_PER_POINT)
            xl_image.height = max(1.0, (image.location.y1 - image.location.y0) * PIXELS_PER_POINT)
            col = _locate(xs, image.location.x0)
            row = _locate(ys, image.location.y0)
            ws.add_image(xl_image, f"{get_column_letter(col + 1)}{row + 1}")
        except Exception as exc:
            issues.append(("IMAGE_NOT_EMBEDDED", page.page_number,
                           f"{image.id}: could not embed image ({type(exc).__name__}); compare with the source PDF."))


def _validate_image_bytes(data: bytes) -> None:
    """Raise now if the image is corrupt, rather than only at wb.save() time
    (where a single bad image would abort the whole export instead of being
    isolated to one disclosed IMAGE_NOT_EMBEDDED warning)."""
    from PIL import Image as PILImage
    with PILImage.open(BytesIO(data)) as probe:
        probe.verify()


def _open_pil_image(buffer: BytesIO):
    from PIL import Image as PILImage
    return PILImage.open(buffer)


def _add_page_sheet(wb: "Workbook", page, issues: list) -> None:
    """Approximate the PDF page's visual layout as one worksheet per page.

    Table_N sheets stay the authoritative, type-aware export; this sheet is
    an additional, purely visual overlay built from the same geometry
    (column_widths/row_heights/row_span/col_span) digital.py already
    computes. A placement collision degrades visibly - a _Warnings entry,
    content still fully intact in Table_N/_Original - rather than ever
    dropping data or crashing the export.
    """
    if not page.tables and not page.blocks:
        return
    xs, ys = _build_page_grid(page)
    if (len(xs) - 1) * (len(ys) - 1) > 5000:
        issues.append(("VISUAL_GRID_TOO_DENSE", page.page_number,
                       "Page layout too dense for a visual grid; falling back to plain text for this page."))
        ws = wb.create_sheet(f"Pagina_{page.page_number}")
        has_text = False
        for line in page.extracted_text.splitlines():
            put_text(ws.cell(ws.max_row + 1 if has_text else 1, 1), line)
            has_text = True
        for image in page.images:
            issues.append(("IMAGE_NOT_EMBEDDED", page.page_number,
                           f"{image.id}: page layout too dense for a visual grid; images are not embedded "
                           "in the plain-text fallback. Compare with the source PDF."))
        return
    if len(xs) - 1 > 16384 or len(ys) - 1 > 1048576:
        raise ValueError("Page grid exceeds Excel dimensions")

    ws = wb.create_sheet(f"Pagina_{page.page_number}")
    col_widths = [_col_width(xs, i) for i in range(len(xs) - 1)]

    # Positions are computed once, up front, for every table cell and block -
    # both the column-widening pass below and the writing loops need them,
    # and computing them twice would risk the two copies drifting apart.
    table_positions = []
    table_cell_positions = []
    for table in page.tables:
        row0 = _locate(ys, table.location.y0)
        col0 = _locate(xs, table.location.x0)
        table_positions.append((row0, _locate(ys, table.location.y1), col0))
        for cell in table.cells:
            row_start, col_start = row0 + cell.row_index, col0 + cell.col_index
            row_end = min(len(ys) - 1, max(row_start + 1, row_start + cell.row_span))
            col_end = min(len(xs) - 1, max(col_start + 1, col_start + cell.col_span))
            table_cell_positions.append((table, cell, row_start, row_end, col_start, col_end))

    block_positions = [(_locate(ys, block.location.y0), _locate(ys, block.location.y1), _locate(xs, block.location.x0))
                       for block in page.blocks]
    block_cell_positions = []
    for block, (row_start, row_end_raw, col_start), col_end_raw in zip(
            page.blocks, block_positions, _block_col_ends(xs, block_positions, table_positions)):
        row_end = min(len(ys) - 1, max(row_start + 1, row_end_raw))
        col_end = min(len(xs) - 1, max(col_start + 1, col_end_raw))
        block_cell_positions.append((block, row_start, row_end, col_start, col_end))

    for _, cell, _, _, col_start, col_end in table_cell_positions:
        _widen_for_content(col_widths, col_start, col_end, cell.content)
    for block, _, _, col_start, col_end in block_cell_positions:
        _widen_for_content(col_widths, col_start, col_end, block.content)

    for i, width in enumerate(col_widths):
        ws.column_dimensions[get_column_letter(i + 1)].width = width
    # Row heights are sized AFTER every cell/block is placed below (see
    # row_height_pt), not here from raw PDF geometry alone: a cell whose text
    # wraps into more lines at Excel's (approximate, possibly widened above)
    # column width than it occupied in the source PDF needs a taller row than
    # the PDF geometry alone implies, or Excel clips it to a sliver of its
    # first line - a real defect found rendering real documents through
    # actual Excel, not just openpyxl round-trips (narrow columns clipped
    # "REFACCIONES" to "REF").
    row_height_pt = [ys[j + 1] - ys[j] for j in range(len(ys) - 1)]

    def bump_row_height(row_start: int, row_end: int, col_start: int, col_end: int,
                         text: str, runs: list[TextRun]) -> None:
        needed = _required_row_height(text, runs, col_widths, col_start, col_end)
        span = row_end - row_start
        if span <= 1:
            if 0 <= row_start < len(row_height_pt):
                row_height_pt[row_start] = max(row_height_pt[row_start], needed)
        else:
            current = sum(row_height_pt[row_start:row_end])
            if current < needed and row_end - 1 < len(row_height_pt):
                row_height_pt[row_end - 1] += needed - current

    occupied: set[tuple[int, int]] = set()
    for table, cell, row_start, row_end, col_start, col_end in table_cell_positions:
        span = _rect_cells(row_start, row_end, col_start, col_end)
        if occupied & span:
            issues.append(("VISUAL_LAYOUT_COLLISION", page.page_number,
                           f"{table.id} R{cell.row_index}C{cell.col_index}: overlapped another element "
                           "on the page overlay; only the Table_N/_Original value is authoritative."))
            continue
        occupied |= span
        target = ws.cell(row_start + 1, col_start + 1)
        runs = cell.runs if cell.runs else [TextRun(content=cell.content)]
        put_rich_text(target, runs)
        if row_end - row_start > 1 or col_end - col_start > 1:
            ws.merge_cells(start_row=row_start + 1, start_column=col_start + 1,
                            end_row=row_end, end_column=col_end)
        # A row-span>1 cell (e.g. a SUBTOTAL/IVA/TOTAL label with no internal
        # ruling) carries embedded newlines; without wrap_text Excel shows
        # embedded line breaks only on one squashed line, not stacked lines.
        target.alignment = Alignment(wrap_text=True, vertical="top")
        if table.has_header and cell.row_index < table.header_rows:
            target.font = Font(bold=True)
        if cell.fill_color:
            target.fill = PatternFill(fgColor=_argb(cell.fill_color), fill_type="solid")
        bump_row_height(row_start, row_end, col_start, col_end, cell.content, runs)

    for block, row_start, row_end, col_start, col_end in block_cell_positions:
        span = _rect_cells(row_start, row_end, col_start, col_end)
        if occupied & span:
            issues.append(("VISUAL_LAYOUT_COLLISION", page.page_number,
                           f"{block.id}: overlapped another element on the page overlay; "
                           "only the extracted text is authoritative."))
            continue
        occupied |= span
        target = ws.cell(row_start + 1, col_start + 1)
        runs = block.runs if block.runs else [TextRun(content=block.content)]
        put_rich_text(target, runs)
        if row_end - row_start > 1 or col_end - col_start > 1:
            ws.merge_cells(start_row=row_start + 1, start_column=col_start + 1,
                            end_row=row_end, end_column=col_end)
        target.alignment = Alignment(wrap_text=True, vertical="top")
        if block.fill_color:
            target.fill = PatternFill(fgColor=_argb(block.fill_color), fill_type="solid")
        bump_row_height(row_start, row_end, col_start, col_end, block.content, runs)

    for j, height in enumerate(row_height_pt):
        ws.row_dimensions[j + 1].height = height
    _embed_page_images(ws, page, xs, ys, issues)


def export_xlsx(document: DocumentIR, *, numeric_columns: dict[str, dict[int, str]] | None = None) -> bytes:
    """Numeric conversion requires an explicit table/column map and en_US syntax.

    Example: {'p1_t1': {1: 'integer', 2: 'currency', 3: 'currency'}}.
    Dates and identifiers stay text. Excel's 15-digit precision is enforced.
    """
    numeric_columns = numeric_columns or {}
    wb = Workbook()
    wb.remove(wb.active)
    original = wb.create_sheet("_Original")
    original.append(["Table", "Page", "Row", "Column", "Original text"])
    issues = []
    for i, table in enumerate(document.get_all_tables(), 1):
        ws = wb.create_sheet(f"Table_{i}")
        if table.rows > 1048576 or table.columns > 16384:
            raise ValueError("Table exceeds Excel dimensions")
        occupied = set()
        for source in table.cells:
            r, c = source.row_index, source.col_index
            if not (0 <= r < table.rows and 0 <= c < table.columns) or (r, c) in occupied:
                raise ValueError("Invalid or duplicate cell coordinates")
            occupied.add((r, c))
            target = ws.cell(r + 1, c + 1)
            put_text(target, source.content)
            original.append([table.id, table.page_number, r, c, None])
            put_text(original.cell(original.max_row, 5), source.content)
            kind = numeric_columns.get(table.id, {}).get(c)
            if kind and r > 0 and source.content.strip():
                if kind not in {"integer", "decimal", "currency"}:
                    raise ValueError("Unsupported numeric type")
                cleaned = source.content.strip()
                if kind == "currency":
                    cleaned = cleaned.removeprefix("$").strip()
                pattern = r"-?(?:0|[1-9]\d*|[1-9]\d{0,2}(?:,\d{3})+)(?:\.\d+)?"
                try:
                    if not re.fullmatch(pattern, cleaned):
                        raise ValueError()
                    value = Decimal(cleaned.replace(",", ""))
                    if (len(value.as_tuple().digits) > 15 or
                        (value != 0 and not -307 <= value.adjusted() <= 307) or
                        (kind == "currency" and value != value.quantize(Decimal("0.01"))) or
                        (kind == "integer" and value != value.to_integral_value())):
                        raise ValueError()
                    target.value = int(value) if kind == "integer" else value
                    target.number_format = "0" if kind == "integer" else '#,##0.00' if kind == "currency" else "General"
                except (ValueError, InvalidOperation):
                    issues.append(("NUMERIC_VALUE_KEPT_AS_TEXT", table.page_number,
                                   f"{table.id} R{r + 1} C{c + 1}: ambiguous format or precision; original retained."))
            target.alignment = Alignment(wrap_text=True, vertical="top")
            if table.has_header and r < table.header_rows:
                target.font = Font(bold=True)
            for issue in source.warnings:
                issues.append((issue.code, issue.page_number, issue.message))
        ws.freeze_panes = "A2" if table.has_header else None
        for issue in table.warnings:
            issues.append((issue.code, issue.page_number, issue.message))
    # Tables only ever cover the ruled grids on a page. Anything else -
    # letterhead, names, totals outside a ruled box, footer notes - lives
    # only in this full-text sheet; without it, a page with any detected
    # table would otherwise lose everything not inside that table's bbox.
    text_sheet = wb.create_sheet("Texto completo", 0)
    has_text = False
    for page in document.pages:
        for line in page.extracted_text.splitlines():
            put_text(text_sheet.cell(text_sheet.max_row + 1 if has_text else 1, 1), line)
            has_text = True
    for page in document.pages:
        _add_page_sheet(wb, page, issues)
    if not document.get_all_tables():
        issues.append(("NO_TABLES", 1, "No ruled tables detected; only extracted text is exported."))
    origin = wb.create_sheet("_Origin")
    for key, value in [("Source SHA256", document.source_hash), ("Schema", document.schema_version),
                       ("Source page count", str(document.page_count)),
                       ("Exported source pages", ", ".join(str(p.page_number) for p in document.pages)),
                       ("Numeric syntax", "en_US; explicit columns only"),
                       ("Quality", "unverified; needs_review")]:
        origin.append([key, None])
        put_text(origin.cell(origin.max_row, 2), value)
    origin.append(["Visual page sheets",
                   "Pagina_N sheets approximate the source PDF page layout (purely visual; Table_N/_Original "
                   "remain authoritative). Excel column widths are an approximation of PDF point widths, not "
                   "pixel-exact; row heights are enlarged from PDF geometry when wrapped text needs more lines "
                   "than the original single line. Warning codes: VISUAL_GRID_TOO_DENSE, VISUAL_LAYOUT_COLLISION, "
                   "IMAGE_NOT_EMBEDDED, TABLE_LAYOUT_ENRICHMENT_SKIPPED."])
    for engine in document.engines_used:
        origin.append([engine.engine_name, engine.engine_version])
    for table in document.get_all_tables():
        origin.append([table.id, f"page {table.page_number}; bbox {table.location.model_dump()}"])
        if table.continuation_of:
            origin.append([f"{table.id} continuation candidate", table.continuation_of])
    for issue in document.warnings + [w for p in document.pages for w in p.warnings]:
        issues.append((issue.code, issue.page_number, issue.message))
    ws = wb.create_sheet("_Warnings")
    ws.append(["Code", "Page", "Message"])
    for code, page, message in issues:
        ws.append([None, page, None])
        put_text(ws.cell(ws.max_row, 1), code)
        put_text(ws.cell(ws.max_row, 3), message)
    result = BytesIO()
    # Metadata in an externally supplied IR is also untrusted text.
    for sheet in wb:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    put_text(cell, cell.value)
    wb.save(result)
    return result.getvalue()
