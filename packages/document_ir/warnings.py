"""One deduplicated view of extraction and export issues, with provenance."""
from __future__ import annotations

from packages.document_ir.models import ContentWarning, DocumentIR


def collect_warnings(document: DocumentIR) -> list[ContentWarning]:
    result = []
    seen = set()

    def add(issue: ContentWarning, **context):
        update = {key: value for key, value in context.items() if getattr(issue, key) is None}
        issue = issue.model_copy(update=update) if update else issue
        key = issue.model_dump_json(exclude_none=True)
        if key not in seen:
            seen.add(key)
            result.append(issue)

    for issue in document.warnings:
        add(issue)
    for page in document.pages:
        for issue in page.warnings:
            add(issue)
        for block in page.blocks:
            for issue in block.warnings:
                add(issue)
        for table in page.tables:
            for issue in table.warnings:
                add(issue, table_id=table.id)
            for cell in table.cells:
                for issue in cell.warnings:
                    add(issue, table_id=table.id, row_index=cell.row_index, col_index=cell.col_index)
    return result


def add_export_warnings(document: DocumentIR, issues: list[tuple], output_format: str) -> None:
    """Persist exporter-only issues so UI, IR and downloadable reports see them."""
    seen = {issue.model_dump_json(exclude_none=True) for issue in document.warnings}
    for code, page_number, message in issues:
        issue = ContentWarning(level="warning", code=code, page_number=page_number,
                               message=message, output_format=output_format)
        key = issue.model_dump_json(exclude_none=True)
        if key not in seen:
            document.warnings.append(issue)
            seen.add(key)
