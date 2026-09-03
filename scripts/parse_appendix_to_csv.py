#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Parse the thesis *Appendix* PDF into a single CSV of KTU text records.

The Appendix (thesis pp. 506-582) is one continuous 11-column table listing
every KTU text with its excavation number, genre and find-spot:

    KTU         KTU text number ("1.1", "9.288", "10.1")
    RS Number   excavation number ("3.361", "1-11.[048]", "RIH 84/04")
    Genre       myth / ritual / list (sacrifices) / letter / ...
    Locus       find-spot code (GP, PH, Acr, PC, PS, PN, Rap, Ršp, surface, ...)
    Room        room number or named locus ("Court V (oven)")
    Point       find-spot point number, or a range ("338, 341, 343")
    Depth       depth in metres, or a range ("0.30-0.40")
    Disputed?   disputed find-spot? (y/n)
    TEO, I, p.  page reference in Bordreuil & Pardee, TEO I
    SAU, p.     page reference in van Soldt, SAU
    Comments    free-text notes

Two kinds of multi-line structure are flattened:

*   **Merged KTU cells.** One KTU number can span several excavation numbers
    (KTU 1.2 = RS 3.367 + RS 3.346), each with its own find-spot. The spanned
    rows leave the KTU cell blank; here it is forward-filled so every emitted
    row is self-contained, and ``is_subrow`` marks the rows that were filled.
    ``genre`` is *not* forward-filled -- the source leaves it blank on some
    sub-rows and repeats it on others, and flattening that would erase the
    distinction. Fill it downstream if you want it.
*   **Wrapped cells.** A long genre, room, locus or comment runs onto further
    lines with every other cell blank. Those lines carry neither a KTU nor an
    excavation number, and are re-joined into the cell they continue.

Nothing is discarded except the repeated "Appendix <page>" running head and the
single column-header row on the first page. Every other word is placed into
exactly one column, by its x position against the boundaries the header row
defines -- the column grid is identical on all 77 pages.

Text extraction shells out to poppler's ``pdftotext -bbox-layout``, which emits
word-level bounding boxes as XHTML and already un-rotates the landscape pages,
so the parser needs no third-party libraries.

``Appendix.pdf`` is downloaded from the White Rose eTheses deposit and checked
against a pinned SHA-256 if it is not already present (see ``sources.py``).

    uv run --no-project scripts/parse_appendix_to_csv.py

or point it at custom locations:

    uv run --no-project scripts/parse_appendix_to_csv.py --input Appendix.pdf \
        --output output/appendix.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import APPENDIX, PROJECT_ROOT, SourceError, ensure  # noqa: E402

XHTML = "{http://www.w3.org/1999/xhtml}"

# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

# Column boundaries (x, in PDF points), taken midway between the right edge of
# one column's widest cell and the left edge of the next. The grid is fixed for
# the whole Appendix: every page places its cells on exactly these left edges
# (72.0, 102.8, 155.7, 263.7, 322.4, 381.1, 439.8, 497.7, 542.7, 587.7, 623.6),
# so a word's x position alone identifies its column.
COLUMNS = (
    "ktu",
    "rs_number",
    "genre",
    "locus",
    "room",
    "point",
    "depth",
    "disputed",
    "teo_i_p",
    "sau_p",
    "comments",
)
BOUNDARIES = (100.0, 153.0, 262.0, 322.0, 380.0, 439.0, 496.0, 540.0, 585.0, 621.0)

# Words on the same printed line share a yMin to within a couple of points; a
# font change inside a cell shifts it by ~1.2pt, while the line pitch is ~9.2pt.
LINE_TOLERANCE = 4.0

# The running head ("Appendix" + page number) sits at y=122.4 on every page; the
# table itself never starts above y=149.
HEAD_Y = 140.0

# Cells that identify the one column-header row, on the first page only.
HEADER_CELLS = {"ktu": "KTU", "rs_number": "RS Number"}

# A record starts on any line that fills either of the two identifying columns.
# Most sub-rows carry only an excavation number under a merged KTU cell; a few
# cross-reference stubs ("7.26  = KTU 7.1") carry only a KTU number.
RECORD_COLUMNS = ("ktu", "rs_number")

# --------------------------------------------------------------------------- #
# Ugaritic transliteration repair
# --------------------------------------------------------------------------- #

# The Appendix is set in the same legacy transliteration font as the Workbooks,
# whose glyphs were extracted as the "wrong" Unicode code points. This is the
# map from scripts/parse_workbooks_to_csv.py, and only four of its letters occur
# here at all -- each independently confirmed in context: R¡p -> Ršp (the house
# of Rašapabu, distinct from the 'Rap' of Rāpānu), (¡umma -> (šumma (the
# Akkadian omen protasis), un® -> unṯ (a service obligation), ˙mr[m] -> ḥmr[m]
# ("donkeys"), (ãbq) -> (ṭbq) (the place name Ṭbq).
UGARITIC_LETTER_MAP = {
    "¡": "š",  # U+00A1 inverted-! -> s with caron
    "®": "ṯ",  # U+00AE registered -> t with line below
    "Θ": "ṯ",  # a variant glyph for the same letter
    "˙": "ḥ",  # U+02D9 dot-above -> h with dot below
    "ß": "ṣ",  # U+00DF sharp-s   -> s with dot below
    "∆": "ḫ",  # U+2206 increment -> h with breve below
    "ƒ": "ḏ",  # U+0192 florin    -> d with line below
    "ã": "ṭ",  # U+00E3 a-tilde   -> t with dot below
    "\\": "ġ",  # U+005C backslash -> g with dot above
    "∞": "ś",  # infinity         -> s with acute
    "Ω": "ẓ",  # ohm              -> z with dot below
}
_UG_TRANS = str.maketrans(UGARITIC_LETTER_MAP)

# The Workbooks' ayin repair is deliberately NOT applied here. In the Workbooks
# ``‘`` doubles as the ayin letter; in the Appendix all 555 of them open a
# quotation ("SAU has ‘pt unspecified’") in English and French prose, where a
# French elision ("n’existera") would break the opener/closer pairing and turn a
# quotation mark into a consonant.

# The author's source has a find-and-replace slip: a case-insensitive
# "pn" -> "P.N." replacement corrupted the find-spot code "PN" (Palais Nord of
# Ras Ibn Hani -- its sibling "PS"/Palais Sud survives clean, and no clean "PN"
# is left). All 152 occurrences are in the locus column, so the repair is
# confined to it.
PN_COLUMN = "locus"


def fix_ugaritic(text: str) -> str:
    """Repair legacy-font transliteration to standard Ugaritic Unicode."""
    return text.translate(_UG_TRANS) if text else text


def repair_pn(text: str, column: str) -> str:
    if column != PN_COLUMN or "P.N." not in text:
        return text
    return text.replace("P.N.", "PN")


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


@dataclass
class Word:
    x: float
    y: float
    text: str


@dataclass
class Record:
    page: str
    is_subrow: bool
    cells: dict[str, list[str]] = field(
        default_factory=lambda: {name: [] for name in COLUMNS}
    )

    def add(self, column: str, text: str) -> None:
        self.cells[column].append(text)

    def to_row(self, ktu: str) -> dict[str, str]:
        row = {"page": self.page, "ktu": ktu, "is_subrow": "1" if self.is_subrow else ""}
        for column in COLUMNS:
            if column == "ktu":
                continue
            value = re.sub(r"\s+", " ", " ".join(self.cells[column])).strip()
            row[column] = repair_pn(fix_ugaritic(value), column)
        return row


def column_for(x: float) -> str:
    for index, boundary in enumerate(BOUNDARIES):
        if x < boundary:
            return COLUMNS[index]
    return COLUMNS[-1]


def extract_words(pdf_path: Path) -> ET.Element:
    result = subprocess.run(
        ["pdftotext", "-bbox-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return ET.fromstring(result.stdout)


def page_lines(page: ET.Element) -> tuple[str, list[list[Word]]]:
    """Split one page into its running-head page number and its printed lines."""
    words = [
        Word(float(w.get("xMin")), float(w.get("yMin")), (w.text or "").strip())
        for w in page.iter(XHTML + "word")
    ]
    words = [w for w in words if w.text]
    head = [w for w in words if w.y < HEAD_Y]
    number = max((w for w in head), key=lambda w: w.x).text if head else ""

    lines: list[list[Word]] = []
    for word in sorted((w for w in words if w.y >= HEAD_Y), key=lambda w: (w.y, w.x)):
        if lines and abs(word.y - lines[-1][0].y) <= LINE_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    return number, [sorted(line, key=lambda w: w.x) for line in lines]


def line_cells(line: list[Word]) -> dict[str, list[str]]:
    cells: dict[str, list[str]] = {}
    for word in line:
        cells.setdefault(column_for(word.x), []).append(word.text)
    return cells


def is_header(cells: dict[str, list[str]]) -> bool:
    return all(
        " ".join(cells.get(column, [])) == expected
        for column, expected in HEADER_CELLS.items()
    )


def parse(pdf_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    root = extract_words(pdf_path)
    records: list[Record] = []
    warnings: list[str] = []

    for page in root.iter(XHTML + "page"):
        number, lines = page_lines(page)
        for line in lines:
            cells = line_cells(line)
            if is_header(cells):
                continue
            starts_record = any(column in cells for column in RECORD_COLUMNS)
            if starts_record:
                records.append(Record(page=number, is_subrow="ktu" not in cells))
            elif not records:
                warnings.append(
                    f"p{number}: dropped a continuation line before any record: "
                    + " | ".join(f"{c}={' '.join(v)}" for c, v in sorted(cells.items()))
                )
                continue
            for column, parts in cells.items():
                for part in parts:
                    records[-1].add(column, part)

    rows: list[dict[str, str]] = []
    ktu = ""
    for record in records:
        printed = re.sub(r"\s+", " ", " ".join(record.cells["ktu"])).strip()
        if printed:
            ktu = printed
        elif not ktu:
            warnings.append(f"p{record.page}: sub-row with no KTU number to inherit")
        rows.append(record.to_row(ktu))
    return rows, warnings


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    fieldnames = ["page", "ktu", "is_subrow", *(c for c in COLUMNS if c != "ktu")]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse the thesis Appendix PDF into a CSV of KTU text records."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=None,
        help="source PDF (default: ./Appendix.pdf, downloaded if absent)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=PROJECT_ROOT / "output" / "appendix.csv",
        help="destination CSV",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="fail instead of fetching a missing source PDF",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.input is None:
            pdf_path = ensure(APPENDIX, download=not args.no_download)
        else:
            pdf_path = args.input.resolve()
            if not pdf_path.exists():
                raise SourceError(f"{pdf_path} does not exist")
    except SourceError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    rows, warnings = parse(pdf_path)
    write_csv(rows, args.output.resolve())
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"Wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
