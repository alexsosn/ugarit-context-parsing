#!/usr/bin/env python3
"""Report source-safe structural shapes of Burns Column-C references.

The report replaces Roman-numeral columns with ``R``, Arabic line numbers with
``N``, and all remaining words with ``W``. It never prints the source reference
text, headwords, comments, or any generated Burns-derived records.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_real_source import _load_burns  # noqa: E402

_ROMAN = r"[IVXLCDM]+"
_SPACE = re.compile(r"\s+")


def structural_shape(value: str) -> str:
    text = unicodedata.normalize("NFC", value.strip())
    # Sentinels are deliberately non-alphabetic so the later word scrub cannot
    # erase the distinction between Roman column markers and Arabic line nums.
    text = re.sub(_ROMAN, "¤", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+", "#", text)
    text = re.sub(r"[A-Za-zÀ-žʿʾšṯḥṣḫḏṭġśẓ]+", "W", text)
    text = text.replace("¤", "R").replace("#", "N")
    return _SPACE.sub(" ", text).strip()


def main() -> int:
    _rows, annotations, _pdf_counts = _load_burns()
    shapes = Counter(structural_shape(a.references) for a in annotations if a.references.strip())
    section_shapes: dict[str, Counter[str]] = {}
    for annotation in annotations:
        if not annotation.references.strip():
            continue
        section = annotation.section or "(none)"
        section_shapes.setdefault(section, Counter())[structural_shape(annotation.references)] += 1

    print(f"reference_cells={sum(shapes.values())}")
    print(f"distinct_structural_shapes={len(shapes)}")
    print("top_structural_shapes:")
    for shape, count in shapes.most_common(40):
        print(f"{count:5d}\t{shape}")
    print("section_shape_summary:")
    for section in sorted(section_shapes):
        counter = section_shapes[section]
        top = "; ".join(f"{count}:{shape}" for shape, count in counter.most_common(8))
        print(f"{section}\t{sum(counter.values())}\t{top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
