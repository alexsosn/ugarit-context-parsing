# ugarit-context-parsing

Structured extraction of the cultic-vocabulary **Workbooks** into per-worksheet
CSV files and of the thesis **Appendix** into a KTU findspot table, with the
Ugaritic transliteration repaired to standard Unicode. The repository also
ships an installable Workbooks → Text-Fabric materializer for local use and for
Agora/Context-Fabric integration.

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
- [`src/ugarit_context_parsing/`](src/ugarit_context_parsing/) — the installable
  Workbooks CSV/PDF → Text-Fabric converter used by the Agora materializer.
- [`agora.materializer.json`](agora.materializer.json) — Agora v1 declarations
  for user-local CSV and PDF materialization.
- [`CONTEXTUALIST_APPROACH.md`](CONTEXTUALIST_APPROACH.md) — an overview of the
  dissertation's contextualist method, the significance of its annotation
  scheme, and the role of the parser.
- [`output/`](output/) — the local generation target for the ignored CSVs, one
  per source worksheet plus `appendix.csv`. [`output/README.md`](output/README.md)
  documents the column schema, the legacy-font → Unicode transliteration repair
  (verified 99.7 % against the KTU concordance and the DULAT dictionary), and
  the editorial corrections.

## Extracting the source tables

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

## Materializing the Workbooks as Text-Fabric

Install the project in a Python 3.10+ environment:

```bash
python -m pip install .
```

### From generated CSV

The normal parser output may contain both one-level Workbook CSV files and the
root-level `appendix.csv`. The Workbooks materializer deliberately reads only
`*/*.csv`, so the Appendix table is not mixed into the contextual graph.

```bash
ugarit-context-parsing convert output \
  --input-format csv \
  --output tf/burns-workbooks
```

### Directly from the Workbook PDFs

PDF mode uses the existing `parse_workbooks_to_csv.py` parsing implementation;
it does not maintain a second interpretation of the source layout and it never
downloads data during materialization.

```bash
ugarit-context-parsing convert Workbooks \
  --input-format pdf \
  --output tf/burns-workbooks
```

Both paths produce the same TF graph model plus a deterministic
`conversion-report.json`. The required artifact files include `otype.tf`,
`oslots.tf`, and `otext.tf`. Input symlinks are rejected rather than followed or
silently skipped.

### TF graph model

A Burns table row is the TF slot type `record`. The source hierarchy is exposed
through the section types `worksheet`, `section`, and `entry`. Every Workbook
column is retained as a feature, together with relative source-file and row/page
provenance.

The CUC interoperability layer is intentionally narrow:

- exact KTU identifiers such as `1.14` receive the additive
  `cuc_tablet="KTU 1.14"` feature, matching the Copenhagen Ugaritic Corpus tablet
  spelling;
- `language=Ugaritic` follows CUC's language value;
- the Unicode transliteration produced by the existing Workbook parser is kept.

The converter does **not** create CUC `sign`, `word`, `line`, or `column` nodes,
because Burns' contextual tables do not encode the diplomatic text structure
needed to justify them. The generated corpus remains Burns-derived data; it is
not a copy, extension, or replacement of DT-UCPH/cuc.

### Agora materializers

`agora.materializer.json` declares two user-local, network-denied materializers:

- `burns-workbooks-csv-text-fabric`
- `burns-workbooks-pdf-text-fabric`

Agora can install this repository as a Python materializer and execute either
path in its materialization host. Automatic resource → materializer → consumer
composition is an Agora concern and is not asserted by this upstream manifest.
The emitted TF artifact is intended to be loadable by Text-Fabric 13.x and the
Context-Fabric/cfabric-mcp stack.

### Appendix scope

`output/appendix.csv` has a different 11-column KTU catalogue schema. It is
explicitly excluded from the Workbooks materializer; Appendix → TF needs its own
graph/materializer design rather than being coerced into the cultic-vocabulary
row model.

## License and attribution

The source Workbooks and thesis are © Duncan Coe Burns (2003) and are made
available under a **Creative Commons Attribution-NonCommercial-NoDerivs 2.5**
licence (CC BY-NC-ND 2.5).

The CSV files generated under `output/`, and Text-Fabric artifacts generated
from them or directly from the PDFs, are **derived reformatting** of that
material. Because the source licence is **NoDerivatives**, they are intentionally
kept local and are not committed or redistributed by this repository. Do not
redistribute generated CSV/TF artifacts without permission from the copyright
holder. Users can obtain the licensed source files from the link above and run
the parsers/materializer for their own use.
