#!/usr/bin/env python3
"""Aggregate-only structural audit for issue #31.

Downloads the checksum-pinned Burns Workbooks into temporary storage and counts
A-only lines that the current parser heuristic would classify as root labels.
No source text, headwords, roots, references, comments, CSV, or TF output is
printed or persisted.
"""
from __future__ import annotations

import re
import tempfile
from collections import Counter
from pathlib import Path

import pdfplumber

from scripts.parse_workbooks_to_csv import _content_lines, file_bounds, is_anchor, is_headword_only
from scripts.sources import WORKBOOKS, ensure

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9}


def encoded_ordinal(name: str) -> int | None:
    arabic = re.match(r"^\s*(\d+)\b", name)
    if arabic:
        return int(arabic.group(1))
    roman = re.match(r"^\s*([IVX]+)\b", name, re.IGNORECASE)
    if roman:
        return ROMAN.get(roman.group(1).upper())
    return None


def audit_file(path: Path) -> tuple[int, int, int]:
    with pdfplumber.open(str(path)) as pdf:
        lines = _content_lines(pdf, file_bounds(pdf))

    prev_kind = ""
    headword = ""
    current_root_candidates = 0
    openable_root_candidates = 0
    next_a_anchor_candidates = 0

    for i, (_page_no, cells) in enumerate(lines):
        a = cells["A"]
        c = cells["C"]
        other = cells["I"]

        if a.startswith("Section") and not is_anchor(cells) and not c and not other:
            prev_kind = "SECTION"
            headword = ""
            continue

        if is_anchor(cells):
            if a:
                headword = a
                prev_kind = "ANCHOR_A"
            else:
                prev_kind = "ANCHOR"
            continue

        if is_headword_only(cells):
            openable = prev_kind in ("ANCHOR_A", "WRAP")
            nxt = lines[i + 1][1] if i + 1 < len(lines) else None
            next_is_headwordless_data = nxt is not None and is_anchor(nxt) and not nxt["A"]
            closes_bracket = (
                a.endswith((")", "]"))
                or headword.count("(") > headword.count(")")
                or headword.count("[") > headword.count("]")
            )
            if openable and (next_is_headwordless_data or closes_bracket):
                headword = f"{headword} {a}".strip()
                prev_kind = "WRAP"
            else:
                current_root_candidates += 1
                if openable:
                    openable_root_candidates += 1
                if nxt is not None and is_anchor(nxt) and bool(nxt["A"]):
                    next_a_anchor_candidates += 1
                prev_kind = "ROOT"
            continue

        if a:
            headword = f"{headword} {a}".strip()
        prev_kind = "CONT"

    return current_root_candidates, openable_root_candidates, next_a_anchor_candidates


def main() -> int:
    totals: Counter[int] = Counter()
    openable: Counter[int] = Counter()
    next_a: Counter[int] = Counter()

    with tempfile.TemporaryDirectory(prefix="burns-a-only-audit-") as tmp:
        root = ensure(WORKBOOKS, root=Path(tmp))
        dirs = sorted(path for path in root.iterdir() if path.is_dir())
        index = {path.name: i + 1 for i, path in enumerate(dirs)}
        encoded = [encoded_ordinal(path.name) for path in dirs]
        pdfs = sorted(root.glob("*/*.pdf"), key=lambda p: p.relative_to(root).as_posix())

        for pdf in pdfs:
            workbook = index[pdf.parent.name]
            total, opened, followed = audit_file(pdf)
            totals[workbook] += total
            openable[workbook] += opened
            next_a[workbook] += followed

        print(f"workbook_count={len(dirs)}")
        print(f"pdf_count={len(pdfs)}")
        print(f"directory_ordinal_prefix_matches={sum(value is not None for value in encoded)}")
        print(f"directory_ordinals_exact_1_to_9={sorted(value for value in encoded if value is not None) == list(range(1, 10))}")
        for workbook in sorted(index.values()):
            print(
                f"workbook_{workbook}:root_candidates={totals[workbook]},"
                f"openable_root_candidates={openable[workbook]},"
                f"next_a_anchor_candidates={next_a[workbook]}"
            )
        outside_actions = sum(totals[i] for i in totals if i != 9)
        outside_actions_openable = sum(openable[i] for i in openable if i != 9)
        print(f"outside_workbook_9_root_candidates={outside_actions}")
        print(f"outside_workbook_9_openable_root_candidates={outside_actions_openable}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
