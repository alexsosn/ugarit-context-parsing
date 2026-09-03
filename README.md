# ugarit-context-parsing

Structured extraction of the cultic-vocabulary **Workbooks** into per-worksheet
CSV files and of the thesis **Appendix** into a KTU findspot table, with the
Ugaritic transliteration repaired to standard Unicode.

## Source

The worksheet PDFs, the Appendix and the thesis volumes are from:

> Burns, Duncan Coe (2003). *Contents, texts and contexts: a contextualist
> approach to the Ugaritic texts and their cultic vocabulary.* PhD thesis,
> University of Sheffield.
> <https://etheses.whiterose.ac.uk/id/eprint/15038/>

## Contents

- [`scripts/parse_workbooks_to_csv.py`](scripts/parse_workbooks_to_csv.py) — the
  Workbooks parser (45 worksheets → one CSV each).
- [`scripts/parse_appendix_to_csv.py`](scripts/parse_appendix_to_csv.py) — the
  Appendix parser (thesis pp. 506–582 → `output/appendix.csv`), a findspot table
  of every KTU text: excavation number, genre, locus, room, point, depth, and
  the TEO/SAU page references.
- [`scripts/sources.py`](scripts/sources.py) — downloads and unpacks the two
  source deposits, verifying a pinned SHA-256 on each.
- [`CONTEXTUALIST_APPROACH.md`](CONTEXTUALIST_APPROACH.md) — an overview of the
  dissertation's contextualist method, the significance of its annotation
  scheme, and the role of the parser.
- [`output/`](output/) — the local generation target for the ignored CSVs, one
  per source worksheet plus `appendix.csv`. [`output/README.md`](output/README.md)
  documents the column schema, the legacy-font → Unicode transliteration repair
  (verified 99.7 % against the KTU concordance and the DULAT dictionary), and
  the editorial corrections.

## Usage

```bash
uv run --no-project scripts/parse_workbooks_to_csv.py
```

```bash
uv run --no-project scripts/parse_appendix_to_csv.py
```

Each parser downloads and unpacks whatever source it needs before parsing, so
both run from a bare checkout with nothing else in place. Pass `--no-download`
to fail instead of fetching, or `--input` to point at your own copy. To fetch
both sources without parsing:

```bash
uv run --no-project scripts/sources.py
```

The source files (`Workbooks/`, `Appendix.pdf`, thesis volumes) are large and
are not tracked in git. Downloads are checked against a pinned SHA-256 and moved
into place only once that check passes, so an interrupted or altered download
never leaves a half-written input behind.

The Appendix parser needs poppler's `pdftotext` on `PATH` (`brew install
poppler`); it has no Python dependencies.

## License and attribution

The source Workbooks and thesis are © Duncan Coe Burns (2003) and are made
available under a **Creative Commons Attribution-NonCommercial-NoDerivs 2.5**
licence (CC BY-NC-ND 2.5).

The CSV files generated under `output/` are a **derived reformatting** of that
material. Because the source licence is **NoDerivatives**, they are intentionally
excluded from this repository and kept local-only. Do not redistribute them
without permission from the copyright holder. Users can obtain the licensed
source files from the link above and run the parser for their own use.
