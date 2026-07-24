#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""Parse the Ugaritic cultic *Workbooks* PDFs into per-worksheet CSV files.

Each worksheet PDF is a 9-column table (labelled A-I in the source) whose
columns map onto the same scheme used in the dissertation Appendix:

    A -> headword      the divine/personal/geographical name or cultic term
    B -> ktu           KTU (text) number, or "Not attested"
    C -> references    line references / attestations within the text
    D -> locus         find-spot code (GP, PH, Acr, PC, surface, ...)
    E -> room          room number or named locus ("Court V (oven)")
    F -> point         find-spot point number
    G -> depth         depth (metres)
    H -> disputed      disputed find-spot? (y/n)
    I -> comments      free-text notes

The tables use *merged cells*: one headword (A) spans several KTU rows, and one
KTU (B) together with its references (C) spans several locus sub-rows. In the
PDF the spanned rows are blank; here they are forward-filled so every emitted
row is self-contained. Wrapped cells (a long reference list, a multi-line
comment, or a headword that runs onto a second line) are re-joined into a single
cell.

Nothing is discarded except pure boilerplate (the repeated page title, the page
number, and the single A..I column-letter header on the first page). Every other
word is placed into exactly one column.

Run with uv (installs pdfplumber into an isolated environment):

    uv run --no-project scripts/parse_workbooks_to_csv.py

or point it at custom locations:

    uv run --no-project scripts/parse_workbooks_to_csv.py --input Workbooks --output output
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

# Canonical vertical column boundaries (x, in PDF points) for the 9-column
# table. Used as a fallback for pages that draw no cell borders (a chunk of the
# "Cultic Actions" workbook). All 45 worksheets share this layout to within a
# couple of points; per-file boundaries are derived from the ruled pages when
# available and only fall back to these.
CANONICAL_BOUNDS: tuple[float, ...] = (69, 166, 197, 296, 373, 438, 504, 553, 574, 772)

COLS = tuple("ABCDEFGHI")
COL_FIELD = {
    "A": "headword",
    "B": "ktu",
    "C": "references",
    "D": "locus",
    "E": "room",
    "F": "point",
    "G": "depth",
    "H": "disputed",
    "I": "comments",
}
FIELDNAMES = ["source_page", "section", "root", *COL_FIELD.values()]

LINE_Y_TOL = 6.0      # words within this vertical distance form one visual line
COL_PAD = 3.0         # x slack when snapping a word to a column
HEADER_BAND_TOP = 145  # everything above this y is page title / page number


# --------------------------------------------------------------------------- #
# Ugaritic transliteration repair
# --------------------------------------------------------------------------- #
# The worksheets are set in a legacy transliteration font whose glyphs were
# extracted as the "wrong" Unicode code points. Each maps 1:1 onto a standard
# Ugaritic transliteration letter; every value below was verified against the
# KTU concordance in dulat's udb_cache database (e.g. \zr -> ġzr "hero",
# ∞∞wm -> śśwm "horses", Ωr -> ẓr, kΘr -> kṯr "Kothar").
UGARITIC_LETTER_MAP = {
    "¡": "š",        # U+00A1 inverted-! -> s with caron
    "®": "ṯ",        # U+00AE registered -> t with line below
    "Θ": "ṯ",   # Θ  a variant glyph for the same letter
    "˙": "ḥ",        # U+02D9 dot-above -> h with dot below
    "ß": "ṣ",        # U+00DF sharp-s   -> s with dot below
    "∆": "ḫ",        # U+2206 increment -> h with breve below
    "ƒ": "ḏ",        # U+0192 florin    -> d with line below
    "ã": "ṭ",        # U+00E3 a-tilde   -> t with dot below
    "\\": "ġ",       # U+005C backslash -> g with dot above
    "∞": "ś",   # ∞ infinity       -> s with acute
    "Ω": "ẓ",   # Ω ohm            -> z with dot below
}
_UG_TRANS = str.maketrans(UGARITIC_LETTER_MAP)
# Glyphs that count as a transliteration consonant/vowel, so a ‘ touching one is
# the ayin letter rather than an English quotation mark.
_UG_LETTER = set("abgdhwzyklmnspqrtiu") | set(UGARITIC_LETTER_MAP) | set("šṯḥṣḫḏṭġśẓ")


def _resolve_ayin(text: str) -> str:
    """Turn ``‘`` into ayin ``ʿ`` where it is a letter, keeping gloss quotes.

    ``‘`` (U+2018) doubles as the ayin letter (``b‘l``) and as an opening gloss
    quote (``(‘earth’)``); ``’`` (U+2019) is only ever a closing gloss quote
    (aleph is written ``a/i/u`` in this system, never ``’``). A ``‘`` pressed
    against a consonant is always ayin; an isolated ``‘`` that is later closed by
    a ``’`` is a quote pair and is left alone; any opener with no closer was a
    word-initial ayin.
    """
    chars = list(text)
    stack: list[int] = []
    for i, ch in enumerate(text):
        if ch == "‘":            # ‘
            prev = text[i - 1] if i else ""
            if prev in _UG_LETTER:
                chars[i] = "ʿ"        # ayin bound to the preceding consonant
            else:
                stack.append(i)       # word-initial ayin, or an opening quote
        elif ch == "’":          # ’
            if stack:
                stack.pop()           # pairs with an opening quote -> leave both
    for i in stack:                   # openers with no closer were ayin
        chars[i] = "ʿ"
    return "".join(chars)


def fix_ugaritic(text: str) -> str:
    """Repair legacy-font transliteration to standard Ugaritic Unicode."""
    if not text:
        return text
    return _resolve_ayin(text).translate(_UG_TRANS)


# The author's source has a find-and-replace slip: a case-insensitive
# "pn" -> "P.N." replacement corrupted two different things. Lowercase Ugaritic
# "pn" inside a word (ṣpn -> ṣP.N., ḫrpnt -> ḫrP.N.t) is restored to "pn"; the
# uppercase find-spot code "PN" (Palais Nord — its sibling "PS"/Palais Sud
# survives clean, but no clean "PN" is left) is restored to "PN" in the locus
# column. Genuine "(P.N.)" / "Personal Name" annotations are left untouched.
_UG_PN_RE = re.compile(r"(?<=[a-zšṯḥṣḫḏṭġśẓʿ])P\.N\.")


def repair_pn(text: str, column: str) -> str:
    if "P.N." not in text:
        return text
    if column == "locus":
        return text.replace("P.N.", "PN")
    return _UG_PN_RE.sub("pn", text)


# Editorial corrections. Each key is a headword token reproduced faithfully from
# a slip in the printed workbook (verified glyph-by-glyph against the source PDF);
# the value is the correct reading supplied by the editor. Applied to headword
# and root tokens only, with any trailing markers (* † ! ?) preserved.
HEADWORD_CORRECTIONS = {
    "mssr": "msrr",      # metathesis in the source (KTU 1.14)
    "šmald": "šmal",     # spurious final d (KTU 1.109)
    "ʿtrt": "ʿṯtrt",     # omitted ṯ — the name ʿṯtrt / Athtart (KTU 4.125)
    "ʿmpʿh": "ʿmph",     # spurious second ayin (KTU 1.113)
    "hrnm": "hrnmy",     # omitted final y — the GN Hrnmy
    "yitdb": "yitbd",    # d/b metathesis (KTU 1.14)
}
_MARKERS = "*†!?"


def apply_corrections(headword: str) -> str:
    """Replace known mis-printed headword tokens with the editor's readings."""
    if not headword:
        return headword
    fixed: list[str] = []
    for token in headword.split(" "):
        base = token.rstrip(_MARKERS)
        if base in HEADWORD_CORRECTIONS:
            fixed.append(HEADWORD_CORRECTIONS[base] + token[len(base):])
        else:
            fixed.append(token)
    return " ".join(fixed)


def collapse(xs: list[float], gap: float = 6.0) -> list[float]:
    """Collapse near-duplicate coordinates (borders are drawn as thin rects)."""
    out: list[float] = []
    for x in sorted(xs):
        if not out or x - out[-1] > gap:
            out.append(x)
    return out


def file_bounds(pdf: "pdfplumber.PDF") -> tuple[float, ...]:
    """Derive column boundaries from all vertical edges in the file.

    Returns 10 boundaries (9 columns) when the ruling is clean, otherwise the
    canonical fallback.
    """
    xs: list[float] = []
    for page in pdf.pages:
        xs.extend(e["x0"] for e in page.edges if e["orientation"] == "v")
    bounds = collapse(xs)
    if len(bounds) == 10 and bounds[0] < 90 and bounds[-1] > 750:
        return tuple(bounds)
    return CANONICAL_BOUNDS


def column_of(x: float, bounds: tuple[float, ...]) -> str:
    """Map an x-coordinate to a column letter, clamping the extremes.

    Anything left of the A|B divider is column A; anything right of the H|I
    divider is column I. This guarantees every word lands in some column, so no
    text can be silently dropped off the edges.
    """
    if x < bounds[1] - COL_PAD:
        return "A"
    for i in range(1, 8):
        if x < bounds[i + 1] - COL_PAD:
            return COLS[i]
    return "I"


def cluster_lines(page: "pdfplumber.page.Page") -> list[tuple[float, list[dict]]]:
    """Group a page's words into visual lines, tolerant of diacritic jitter."""
    words = page.extract_words(y_tolerance=3, keep_blank_chars=False)
    words.sort(key=lambda w: (w["top"], w["x0"]))
    lines: list[tuple[float, list[dict]]] = []
    for w in words:
        if lines and abs(w["top"] - lines[-1][0]) <= LINE_Y_TOL:
            lines[-1][1].append(w)
        else:
            lines.append((w["top"], [w]))
    return lines


def line_cells(words: list[dict], bounds: tuple[float, ...]) -> dict[str, str]:
    """Bucket a line's words into columns, preserving left-to-right order."""
    cells: dict[str, list[str]] = defaultdict(list)
    for w in sorted(words, key=lambda w: w["x0"]):
        cells[column_of(w["x0"], bounds)].append(w["text"])
    return {c: " ".join(cells[c]).strip() for c in COLS}


# --------------------------------------------------------------------------- #
# Row assembly
# --------------------------------------------------------------------------- #


class Cell:
    """A mutable text cell shared by every row it spans (a merged cell).

    Because references and comments can wrap onto lines that appear *after* the
    row is created, rows hold a reference to the shared ``Cell`` and the final
    text is read only once the whole file has been processed.
    """

    __slots__ = ("text",)

    def __init__(self, text: str = "") -> None:
        self.text = text

    def append(self, more: str) -> None:
        self.text = f"{self.text} {more}".strip() if self.text else more


@dataclass
class Row:
    source_page: int
    section: str
    root: str
    headword: Cell
    ktu: Cell
    references: Cell
    locus: str
    room: str
    point: str
    depth: str
    disputed: str
    comments: Cell = field(default_factory=Cell)


def is_page_title(cells: dict[str, str]) -> bool:
    text = " ".join(cells.values())
    return "Workbook" in text and "Worksheet" in text


def is_letter_header(cells: dict[str, str]) -> bool:
    return cells["A"] == "A" and cells["B"] == "B" and cells["C"] == "C"


def is_anchor(cells: dict[str, str]) -> bool:
    """A data row: it carries find-spot columns (D-H) or a KTU number (B)."""
    return any(cells[c] for c in "DEFGH") or bool(cells["B"])


def is_headword_only(cells: dict[str, str]) -> bool:
    """A line with text only in column A (a wrapped headword or a root label)."""
    return bool(cells["A"]) and not any(cells[c] for c in "BCDEFGHI")


def _content_lines(pdf: "pdfplumber.PDF", bounds: tuple[float, ...]) -> list[tuple[int, dict[str, str]]]:
    """All non-boilerplate lines of a file, in reading order, with page number."""
    out: list[tuple[int, dict[str, str]]] = []
    for page_no, page in enumerate(pdf.pages, start=1):
        for top, words in cluster_lines(page):
            if top < HEADER_BAND_TOP:
                continue  # page title / page number band
            cells = line_cells(words, bounds)
            if is_page_title(cells) or is_letter_header(cells):
                continue
            out.append((page_no, cells))
    return out


def parse_pdf(path: Path) -> list[dict[str, str]]:
    rows: list[Row] = []
    section = ""
    root = ""
    headword = Cell("")
    ktu = Cell("")
    references = Cell("")
    have_group = False        # has any KTU/headword group started yet?
    last_row: Row | None = None
    prev_kind = ""            # ANCHOR_A | ANCHOR | WRAP | ROOT | CONT | SECTION

    with pdfplumber.open(str(path)) as pdf:
        lines = _content_lines(pdf, file_bounds(pdf))

    for i, (page_no, cells) in enumerate(lines):
        A, B, C = cells["A"], cells["B"], cells["C"]
        D, E, F, G, H, I = (cells[c] for c in "DEFGHI")
        has_locus = any((D, E, F, G, H))

        # Section banner (e.g. "Section α") — updates state, not a row. A new
        # section starts a fresh root grouping.
        if A.startswith("Section") and not is_anchor(cells) and not C and not I:
            section = A
            root = ""
            prev_kind = "SECTION"
            continue

        if is_anchor(cells):
            new_headword = bool(A)
            if new_headword:
                headword = Cell(A)
            if B:                      # a new KTU group begins
                ktu = Cell(B)
                references = Cell(C)
                have_group = True
            elif new_headword or not have_group:
                # new headword without its own KTU, or the very first group:
                # start a fresh KTU/reference group so nothing bleeds across
                # from the previous headword.
                ktu = Cell("")
                references = Cell(C)
                have_group = True
            elif C:
                # locus sub-row of the current KTU that also carries a wrapped
                # fragment of the reference list.
                references.append(C)

            row = Row(
                source_page=page_no,
                section=section,
                root=root,
                headword=headword,
                ktu=ktu,
                references=references,
                locus=D, room=E, point=F, depth=G, disputed=H,
                comments=Cell(I),
            )
            rows.append(row)
            last_row = row
            prev_kind = "ANCHOR_A" if new_headword else "ANCHOR"

        elif is_headword_only(cells):
            # An A-only line is either a headword that wrapped onto a second
            # line, or a root/group label sitting above the forms it groups
            # (the Cultic Actions workbook groups verbal forms under their
            # root). They are told apart structurally:
            #   * a wrap continues the *current* headword — it is only possible
            #     right after that headword (prev line opened it) and is
            #     followed by more of that headword's data (a blank-A row), or
            #     it closes a bracket/paren left open in the headword;
            #   * otherwise the label heads the *next* form and is a root.
            # Whichever way it is read, the text is preserved (headword vs root
            # column) — never dropped.
            openable = prev_kind in ("ANCHOR_A", "WRAP")
            nxt = lines[i + 1][1] if i + 1 < len(lines) else None
            next_is_headwordless_data = nxt is not None and is_anchor(nxt) and not nxt["A"]
            closes_bracket = (
                A.endswith((")", "]"))
                or headword.text.count("(") > headword.text.count(")")
                or headword.text.count("[") > headword.text.count("]")
            )
            if openable and (next_is_headwordless_data or closes_bracket):
                headword.append(A)
                prev_kind = "WRAP"
            else:
                root = A
                prev_kind = "ROOT"

        else:
            # Continuation line carrying wrapped reference and/or comment text
            # (and, rarely, a wrapped headword fragment beside them).
            if A:
                headword.append(A)
            if C and have_group:
                references.append(C)
            if I and last_row is not None:
                last_row.comments.append(I)
            prev_kind = "CONT"

    return [_finalize(r) for r in rows]


def _finalize(r: Row) -> dict[str, str]:
    """Materialise a row, resolving shared cells to their final text.

    Rows whose KTU is "Not attested" carry no find-spot: such a row is a note
    ("outside GP and PH (but cf. ... above)") that physically runs across the
    reference/locus/room columns in the PDF. No such row ever holds real
    find-spot data, so the find-spot columns are folded back into ``references``
    to reunite the note, while the distinct ``comments`` column is left intact.
    """
    out = {
        "source_page": r.source_page,
        "section": r.section,
        "root": r.root,
        "headword": r.headword.text,
        "ktu": r.ktu.text,
        "references": r.references.text,
        "locus": r.locus,
        "room": r.room,
        "point": r.point,
        "depth": r.depth,
        "disputed": r.disputed,
        "comments": r.comments.text,
    }
    if r.ktu.text.startswith("Not attested"):
        spill = [out[c] for c in ("references", "locus", "room", "point", "depth", "disputed") if out[c]]
        out["references"] = " ".join(spill)
        out["locus"] = out["room"] = out["point"] = out["depth"] = out["disputed"] = ""
    for key, value in out.items():
        if isinstance(value, str):
            out[key] = repair_pn(fix_ugaritic(value), key)
    out["headword"] = apply_corrections(out["headword"])
    out["root"] = apply_corrections(out["root"])
    return out


def write_csv(rows: list[dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    root = Path(__file__).resolve().parent.parent
    p.add_argument("--input", type=Path, default=root / "Workbooks",
                   help="Directory of workbook subfolders (default: ./Workbooks)")
    p.add_argument("--output", type=Path, default=root / "output",
                   help="Directory to write CSVs into (default: ./output)")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    input_dir: Path = args.input.resolve()
    output_dir: Path = args.output.resolve()

    pdfs = sorted(input_dir.glob("*/*.pdf"))
    if not pdfs:
        print(f"No worksheet PDFs found under {input_dir}", file=sys.stderr)
        return 1

    grand_total = 0
    for pdf_path in pdfs:
        rel = pdf_path.relative_to(input_dir).with_suffix(".csv")
        out_path = output_dir / rel
        rows = parse_pdf(pdf_path)
        write_csv(rows, out_path)
        grand_total += len(rows)
        print(f"{len(rows):5d} rows  {rel}")

    print(f"\nWrote {grand_total} rows across {len(pdfs)} worksheets into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
