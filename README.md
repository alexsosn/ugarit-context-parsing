# ugarit-context-parsing

Structured extraction of the cultic-vocabulary **Workbooks** into per-worksheet
CSV files, with the Ugaritic transliteration repaired to standard Unicode.

## Source

The worksheet PDFs and the thesis volumes are from:

> Burns, Duncan Coe (2003). *Contents, texts and contexts: a contextualist
> approach to the Ugaritic texts and their cultic vocabulary.* PhD thesis,
> University of Sheffield.
> <https://etheses.whiterose.ac.uk/id/eprint/15038/>

## Contents

- [`scripts/parse_workbooks_to_csv.py`](scripts/parse_workbooks_to_csv.py) — the parser.
- [`CONTEXTUALIST_APPROACH.md`](CONTEXTUALIST_APPROACH.md) — an overview of the
  dissertation's contextualist method, the significance of its annotation
  scheme, and the role of the parser.
- [`output/`](output/) — the local generation target for 45 ignored CSVs, one
  per source worksheet. [`output/README.md`](output/README.md) documents the
  column schema, the legacy-font → Unicode transliteration repair (verified
  99.7 % against the KTU concordance and the DULAT dictionary), and the
  editorial corrections.

## Usage

```bash
uv run --no-project scripts/parse_workbooks_to_csv.py
```

Regenerates every CSV under `output/` from the PDFs in `Workbooks/`.

The source PDFs (`Workbooks/`, thesis volumes, `Appendix.pdf`) are large and are
not tracked in git.

## License and attribution

The source Workbooks and thesis are © Duncan Coe Burns (2003) and are made
available under a **Creative Commons Attribution-NonCommercial-NoDerivs 2.5**
licence (CC BY-NC-ND 2.5).

The CSV files generated under `output/` are a **derived reformatting** of that
material. Because the source licence is **NoDerivatives**, they are intentionally
excluded from this repository and kept local-only. Do not redistribute them
without permission from the copyright holder. Users can obtain the licensed
source files from the link above and run the parser for their own use.
