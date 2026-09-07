from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

WORKBOOK_FIELDS = (
    "source_page", "section", "root", "headword", "ktu", "references",
    "locus", "room", "point", "depth", "disputed", "comments",
)


class SourceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class WorkbookRecord:
    source_file: str
    source_row: int
    source_page: int
    section: str
    root: str
    headword: str
    ktu: str
    references: str
    locus: str
    room: str
    point: str
    depth: str
    disputed: str
    comments: str


@dataclass(frozen=True)
class WorkbookSource:
    root: Path
    records: tuple[WorkbookRecord, ...]
    files: tuple[str, ...]
    tree_sha256: str


def _tree_hash(root: Path, paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        rel = path.relative_to(root).as_posix().encode("utf-8")
        body = path.read_bytes()
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        digest.update(len(body).to_bytes(8, "big"))
        digest.update(body)
    return digest.hexdigest()


def _reject_symlinks(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SourceValidationError(
                f"source contains disallowed symlink: {path.relative_to(root).as_posix()}"
            )


def load_csv_directory(root: str | Path) -> WorkbookSource:
    source_root = Path(root).resolve()
    if not source_root.is_dir():
        raise SourceValidationError(f"source directory does not exist: {root}")
    _reject_symlinks(source_root)
    # The Workbooks parser mirrors the source's one-level category/worksheet
    # layout. Root-level CSVs belong to other products (notably appendix.csv)
    # and must not be pulled into this materializer.
    paths = sorted(
        (p for p in source_root.glob("*/*.csv") if p.is_file()),
        key=lambda p: p.relative_to(source_root).as_posix(),
    )
    if not paths:
        raise SourceValidationError("no Workbook CSV files found")

    records: list[WorkbookRecord] = []
    files: list[str] = []
    expected = list(WORKBOOK_FIELDS)
    for path in paths:
        rel = path.relative_to(source_root).as_posix()
        files.append(rel)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != expected:
                raise SourceValidationError(
                    f"{rel}: Workbook CSV header must be exactly {expected!r}; got {reader.fieldnames!r}"
                )
            for source_row, row in enumerate(reader, start=1):
                assert row is not None
                if all((row.get(field) or "") == "" for field in WORKBOOK_FIELDS):
                    continue
                raw_page = (row.get("source_page") or "").strip()
                try:
                    page = int(raw_page)
                except ValueError as exc:
                    raise SourceValidationError(
                        f"{rel}: row {source_row}: source_page must be an integer >= 1"
                    ) from exc
                if page < 1:
                    raise SourceValidationError(
                        f"{rel}: row {source_row}: source_page must be an integer >= 1"
                    )
                values = {
                    field: (row.get(field) or "")
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
        raise SourceValidationError("Workbook CSV source contains no data rows")
    return WorkbookSource(
        source_root,
        tuple(records),
        tuple(files),
        _tree_hash(source_root, paths),
    )
