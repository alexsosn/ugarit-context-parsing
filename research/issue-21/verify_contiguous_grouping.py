#!/usr/bin/env python3
"""Source-safe audit of Burns semantic grouping for parent issue #21.

Downloads the repository's checksum-pinned Workbooks into temporary storage,
parses them with the existing PDF parser, and compares the historical global
value-dedup partition with the corrected contiguous-run partition. Only
aggregate counts are printed; no Burns rows or field values are persisted or
emitted.
"""
from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

from scripts.parse_workbooks_to_csv import parse_pdf
from scripts.sources import WORKBOOKS, ensure


def main() -> int:
    run_counts: Counter[tuple[str, str, str, str, str, str]] = Counter()
    raw_rows = 0
    previous_key: tuple[str, str, str, str, str, str] | None = None

    with tempfile.TemporaryDirectory(prefix="burns-contiguous-audit-") as tmp:
        root = ensure(WORKBOOKS, root=Path(tmp))
        pdfs = sorted(root.glob("*/*.pdf"), key=lambda path: path.relative_to(root).as_posix())
        for pdf in pdfs:
            rel = pdf.relative_to(root).as_posix()
            previous_key = None
            for row in parse_pdf(pdf):
                raw_rows += 1
                key = (
                    rel,
                    str(row.get("section") or ""),
                    str(row.get("root") or ""),
                    str(row.get("headword") or ""),
                    str(row.get("ktu") or ""),
                    str(row.get("references") or ""),
                )
                if key != previous_key:
                    run_counts[key] += 1
                    previous_key = key

        global_unique_keys = len(run_counts)
        contiguous_groups = sum(run_counts.values())
        repeated_noncontiguous_keys = sum(1 for count in run_counts.values() if count > 1)
        extra_contiguous_groups = contiguous_groups - global_unique_keys
        max_runs_per_key = max(run_counts.values(), default=0)

        print(f"pdfs={len(pdfs)}")
        print(f"raw_rows={raw_rows}")
        print(f"global_unique_keys={global_unique_keys}")
        print(f"contiguous_groups={contiguous_groups}")
        print(f"noncontiguous_repeated_keys={repeated_noncontiguous_keys}")
        print(f"extra_contiguous_groups={extra_contiguous_groups}")
        print(f"max_runs_per_key={max_runs_per_key}")

        # The historical aggregate evidence is valid only if global key
        # deduplication happened to equal the corrected contiguous partition.
        return 0 if extra_contiguous_groups == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
