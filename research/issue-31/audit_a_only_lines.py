#!/usr/bin/env python3
"""Aggregate-only real-source validation for issue #31.

Downloads the checksum-pinned Burns Workbooks into temporary storage and runs
the production PDF parser over every worksheet. Only aggregate counts are
printed; no source text, headwords, roots, references, comments, CSV, or TF
payload is emitted or persisted.
"""
from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

from scripts.parse_workbooks_to_csv import _workbook_ordinal, parse_pdf
from scripts.sources import WORKBOOKS, ensure


def main() -> int:
    parsed_rows: Counter[int] = Counter()
    root_rows: Counter[int] = Counter()

    with tempfile.TemporaryDirectory(prefix="burns-parser-audit-") as tmp:
        root = ensure(WORKBOOKS, root=Path(tmp))
        pdfs = sorted(root.glob("*/*.pdf"), key=lambda p: p.relative_to(root).as_posix())

        for pdf in pdfs:
            workbook = _workbook_ordinal(pdf)
            if workbook is None:
                raise RuntimeError("canonical workbook directory lacks ordinal")
            rows = parse_pdf(pdf)
            parsed_rows[workbook] += len(rows)
            root_rows[workbook] += sum(bool(row["root"]) for row in rows)

        print(f"pdf_count={len(pdfs)}")
        print(f"workbook_ordinals={','.join(str(i) for i in sorted(parsed_rows))}")
        print(f"parsed_rows_total={sum(parsed_rows.values())}")
        print(f"root_rows_total={sum(root_rows.values())}")
        print(f"outside_workbook_9_root_rows={sum(root_rows[i] for i in root_rows if i != 9)}")
        print(f"workbook_9_root_rows={root_rows[9]}")

        if sorted(parsed_rows) != list(range(1, 10)):
            return 2
        if sum(root_rows[i] for i in root_rows if i != 9) != 0:
            return 3
        if root_rows[9] == 0:
            return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
