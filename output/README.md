# Workbooks → CSV

Faithful, lossless conversion of the 45 worksheet PDFs under `Workbooks/` into
one CSV per worksheet, mirroring the source folder structure. Produced by
[`scripts/parse_workbooks_to_csv.py`](../scripts/parse_workbooks_to_csv.py).

The generated CSVs are local-only and ignored by Git because the source is
licensed CC BY-NC-ND 2.5. Do not redistribute them without permission from the
copyright holder.

```bash
uv run --no-project scripts/parse_workbooks_to_csv.py
```

45 files · 13,857 data rows · UTF-8.

## Columns

| column        | source col | meaning |
|---------------|:----------:|---------|
| `source_page` | –          | 1-based page in the source PDF (provenance) |
| `section`     | –          | `Section α / α1 / α2 / β` banner the row falls under |
| `root`        | –          | morphological **root/group label** the row falls under (used by Workbook IX – Cultic Actions, which groups forms under their root; empty elsewhere) |
| `headword`    | A          | the divine / personal / geographical name or cultic term |
| `ktu`         | B          | KTU (text) number, or `Not attested` |
| `references`  | C          | line references / attestations within the text |
| `locus`       | D          | find-spot code (`GP`, `PH`, `Acr`, `PC`, `surface`, …) |
| `room`        | E          | room number or named locus (e.g. `Court V (oven)`) |
| `point`       | F          | find-spot point number |
| `depth`       | G          | depth in metres |
| `disputed`    | H          | disputed find-spot? (`y`/`n`) |
| `comments`    | I          | free-text notes |

The A–I → name mapping matches the scheme in the dissertation `Appendix.pdf`.

## How the source layout is handled

- **Merged cells → forward-filled.** In the PDF one `headword` spans several KTU
  rows, and one `ktu` + its `references` span several find-spot sub-rows (the
  spanned cells are blank). Every output row repeats these so it stands alone.
- **Multi-line cells → rejoined.** A wrapped reference list, a multi-line
  comment, or a headword that runs onto a second line is merged back into a
  single cell (fragments joined with a space).
- **Grouping preserved.** `section` and `root` labels are carried down onto
  every row they cover rather than sitting on their own line.
- **`Not attested` rows.** These carry a prose note ("outside GP and PH (but
  cf. … above)") that physically runs across the reference/locus columns in the
  PDF; it is reunited into `references`, and the find-spot columns are left
  empty (such rows never hold real find-spot data).
- **Dropped as boilerplate:** the repeated page title, page numbers, and the
  single `A B C … I` column-letter header. Nothing else is discarded — every
  other word from every page lands in exactly one cell (verified: 0 source
  tokens missing across all 45 worksheets).

## Ugaritic transliteration

The worksheets are set in a legacy transliteration font whose glyphs were
extracted as the wrong Unicode code points (`¡ ® ˙ ß ∆ …`). The parser repairs
them to standard Ugaritic Unicode. Every mapping was verified against the KTU
concordance (`dulat/app/udb/udb_cache.sqlite`) and the DULAT dictionary
(`dulat/app/data/dulat_cache.sqlite`) — after repair, **99.6 % of headword
tokens are attested Ugaritic words / lemmas**. The rest are inflected forms,
proper names, or `x` placeholders for broken signs.

| legacy | → | | legacy | → | | legacy | → |
|:---:|:---:|---|:---:|:---:|---|:---:|:---:|
| `¡` | š | | `∆` | ḫ | | `\` | ġ |
| `®` | ṯ | | `ƒ` | ḏ | | `∞` | ś |
| `Θ` | ṯ | | `ã` | ṭ | | `Ω` | ẓ |
| `˙` | ḥ | | `ß` | ṣ | | `‘` | ʿ (ayin) |

`‘` (U+2018) is used both as the ayin letter (`b‘l` → `bʿl`) and as an opening
quote around English glosses (`(‘earth’)`); the two are told apart by context, so
gloss quotes are left intact. `’` is always a closing gloss quote (aleph is
written `a/i/u`). Markers `* † ! ?` and epigraphic brackets are kept as-is.

**`P.N.` find-and-replace slip.** The source has a case-insensitive
`pn` → `P.N.` replacement that corrupted two things, both repaired here:
lowercase Ugaritic `pn` inside words (`ṣpn` → `ṣP.N.`, `ḫrpnt` → `ḫrP.N.t`,
`ḫlb ṣpn`) is restored to `pn`, and the find-spot code `PN` (Palais Nord — its
sibling `PS` survived clean, but no clean `PN` was left) is restored to `PN` in
the `locus` column. Genuine "Personal Name" annotations (`(P.N.)`, `Broken
P.N.?`) are left untouched.

## Editorial corrections

A handful of headwords reproduce a slip in the printed source (each verified
glyph-by-glyph against the PDF). The editor's correct readings are applied to the
`headword`/`root` columns and listed here for transparency (see
`HEADWORD_CORRECTIONS` in the parser):

| printed | corrected | reason |
|---|---|---|
| `mssr` | `msrr` | metathesis (KTU 1.14) |
| `šmald` | `šmal` | spurious final *d* (KTU 1.109) |
| `ʿtrt` | `ʿṯtrt` | omitted *ṯ* — the name Athtart (KTU 4.125; 1 row) |
| `ʿmpʿh` | `ʿmph` | spurious second ayin (KTU 1.113) |
| `hrnm` | `hrnmy` | omitted final *y* — the GN Hrnmy |
| `yitdb` | `yitbd` | *d/b* metathesis (KTU 1.14) |

These are token-exact (21 rows in total), so correct forms already present
(e.g. `šmal` "left hand", the 121 genuine `ʿṯtrt` entries) are left untouched.

## Fidelity notes

- Apart from the transliteration repair and the editorial corrections above,
  text is preserved as printed, including epigraphic notation. Some cells
  therefore contain unbalanced `[ ]` brackets (restoration marks) or a trailing
  comma — these are **in the original document**, not extraction artifacts.
- One known edge case: in *Times and Events, Worksheet 1*, the incipit
  `k t‘rb ‘®trt ∆r gb bt mlk*†!` wraps across two lines and its tail (`mlk*†!`)
  is recorded in the `root` column instead of appended to the `headword`. The
  text is retained, just placed one column over. This is the only such case in
  Workbooks I–VIII.
