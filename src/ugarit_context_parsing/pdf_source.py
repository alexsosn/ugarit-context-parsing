from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .source import (
    WORKBOOK_FIELDS,
    SourceValidationError,
    WorkbookRecord,
    WorkbookSource,
    _tree_hash,
)


def parse_workbook_pdf(path: Path) -> list[dict[str, str]]:
    """Use the repository's existing source-sensitive Workbook PDF parser."""
    from scripts.parse_workbooks_to_csv import parse_pdf

    return parse_pdf(path)


def load_pdf_directory(
    root: str | Path,
    *,
    parser: Callable[[Path], list[dict[str, object]]] = parse_workbook_pdf,
) -> WorkbookSource:
    source_root = Path(root).resolve()
    if not source_root.is_dir():
        raise SourceValidationError(f"source directory does not exist: {root}")
    paths = sorted(
        (
            path
            for path in source_root.glob("*/*.pdf")
            if path.is_file() and not path.is_symlink()
        ),
        key=lambda path: path.relative_to(source_root).as_posix(),
    )
    if not paths:
        raise SourceValidationError("no Workbook PDF files found")

    records: list[WorkbookRecord] = []
    files: list[str] = []
    expected = set(WORKBOOK_FIELDS)
    for path in paths:
        rel = path.relative_to(source_root).as_posix()
        files.append(rel)
        rows = parser(path)
        for source_row, row in enumerate(rows, start=1):
            if set(row) != expected:
                raise SourceValidationError(
                    f"{rel}: parsed Workbook row has unexpected fields: {sorted(row)}"
                )
            raw_page = row.get("source_page")
            try:
                page = int(raw_page)  # type: ignore[arg-type]
            except (TypeError, ValueError) as exc:
                raise SourceValidationError(
                    f"{rel}: row {source_row}: source_page must be an integer >= 1"
                ) from exc
            if page < 1:
                raise SourceValidationError(
                    f"{rel}: row {source_row}: source_page must be an integer >= 1"
                )
            values = {
                field: str(row.get(field) or "")
                for field in WORKBOOK_FIELDS
                if field != "source_page"
            }
            records.append(
                WorkbookRecord(
                    source_file=rel,
                    source_row=source_row,
                    source_page=page,
                    **values,
                )
            )
    if not records:
        raise SourceValidationError("Workbook PDF source contains no parsed data rows")
    return WorkbookSource(
        root=source_root,
        records=tuple(records),
        files=tuple(files),
        tree_sha256=_tree_hash(source_root, paths),
    )
