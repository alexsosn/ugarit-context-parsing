# ugarit-context-parsing

Structured extraction of the cultic-vocabulary **Workbooks** into per-worksheet
CSV files and of the thesis **Appendix** into a KTU findspot table, with the
Ugaritic transliteration repaired to standard Unicode. The installable package
also materializes the Workbooks as a **CUC-aligned Text-Fabric feature module**
for local use and Context-Fabric/cfabric-mcp composition.

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
  Workbooks CSV/PDF → CUC feature-module materializer and its legacy standalone
  compatibility converter.
- [`agora.materializer.json`](agora.materializer.json) — the current Agora v1
  declarations for the legacy single-input materializers; see the Agora section
  below for the parent-resource limitation.
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

## Materializing a CUC-aligned Burns feature module

Install the project in a Python 3.10+ environment:

```bash
python -m pip install .
```

The primary product is a feature-only Burns annotation module layered on the
exact reviewed Copenhagen Ugaritic Corpus (CUC) Text-Fabric base. The current
compatibility contract is:

- repository: `DT-UCPH/cuc`
- commit: `ad69400f5446e1c8217af01659c7c10ab00c015b`
- Text-Fabric directory/version: `tf/0.2.8`

The CLI verifies the required CUC files by size and SHA-256 before indexing or
writing a module. It does not download CUC automatically.

### Quickstart with the exact reviewed CUC

CUC acquisition is an explicit user action outside the converter. Clone without
historical blob contents, then check out the reviewed commit directly rather
than using whichever commit upstream `main` points to later:

```bash
git clone --filter=blob:none --no-checkout https://github.com/DT-UCPH/cuc.git cuc
git -C cuc checkout --detach ad69400f5446e1c8217af01659c7c10ab00c015b
git -C cuc rev-parse HEAD
```

The last command should print
`ad69400f5446e1c8217af01659c7c10ab00c015b`. Then materialize generated
Workbook CSVs against that exact base:

```bash
ugarit-context-parsing module output \
  --input-format csv \
  --cuc cuc/tf/0.2.8 \
  --output tf/burns-module
```

The converter itself does not acquire or update CUC. If the checkout is wrong,
incomplete, or modified, the reviewed file and structural fingerprint checks
fail before a Burns module is published.

### CUC compatibility fingerprint

Burns treats the reviewed CUC base as an exact structural dependency, not as a
loose `0.2.x` compatibility range. Alignment uses the CUC `tablet`, `column`,
`line`, and `g_cons` features together with the Text-Fabric warp/navigation
structure. The reviewed base has 146017 `sign`, 27770 `word`, 7616 `line`, 334
`column`, and 279 `tablet` nodes, with `tablet,column,line` as both the section
types and section features.

Every generated Burns feature header keeps the repository/commit/version and
required-files manifest digest and also records a compact deterministic form of
that structural fingerprint. `burns-module-report.json` carries the expanded
fingerprint, including the exact required-file sizes and SHA-256 values used by
the verifier. No local path, machine, platform, or timestamp is part of the
compatibility identity.

Updating Burns to a different CUC commit therefore requires a deliberate
compatibility review: record the candidate fingerprint, prove the old
fingerprint rejects it, rerun the reviewed-CUC alignment/module integration and
Context-Fabric composition checks, and verify that existing CUC node identities
are not silently remapped. Changing only the advertised CUC version is not a
compatibility update.

### From generated CSV

The normal parser output may contain both one-level Workbook CSV files and the
root-level `appendix.csv`. The Workbooks loader deliberately reads only
`*/*.csv`, so the Appendix table is not mixed into the Burns annotations.

```bash
ugarit-context-parsing module output \
  --input-format csv \
  --cuc cuc/tf/0.2.8 \
  --output tf/burns-module
```

### Directly from the Workbook PDFs

PDF mode uses the existing `parse_workbooks_to_csv.py` parsing implementation;
it does not maintain a second interpretation of the source layout and it never
downloads data during materialization.

```bash
ugarit-context-parsing module Workbooks \
  --input-format pdf \
  --cuc cuc/tf/0.2.8 \
  --output tf/burns-module
```

Both source paths feed the same normalization, CUC verification/indexing,
alignment, module-building, reporting, and publishing pipeline. Input symlinks
are rejected rather than followed or silently skipped.

### Feature-module output

A successful module contains exactly these six Text-Fabric node features plus a
deterministic `burns-module-report.json`:

- `burns_annotations.tf` — authoritative lossless Burns annotation payloads
  attached to selected CUC nodes;
- `burns_annotation_ids.tf` — annotation-ID projection;
- `burns_semantic_statuses.tf` — contextual/cultic interpretation-status
  projection;
- `burns_worksheet_roles.tf` — source worksheet-role projection;
- `burns_sections.tf` — Burns section projection;
- `burns_headwords.tf` — Burns headword projection.

The module does **not** emit `otype.tf`, `oslots.tf`, `otext.tf`, or copies of
CUC diplomatic features such as `g_cons.tf`, `tablet.tf`, `column.tf`, or
`line.tf`. CUC owns the node graph; Burns contributes annotations to those
existing nodes. Unresolved, ambiguous, partial, out-of-CUC, and non-textual
source annotations remain accounted for in the module report rather than being
silently promoted to guessed anchors.

With a Context-Fabric/cfabric-mcp version that supports ordered locations, load
the CUC base first and the Burns module second as one logical corpus. The module
writer and integration tests require CUC slot/node counts and navigation to
remain unchanged.

### Deprecated standalone row-slot converter

The older standalone Burns graph remains temporarily available for compatibility:

```bash
ugarit-context-parsing convert output \
  --input-format csv \
  --output tf/burns-workbooks
```

```bash
ugarit-context-parsing convert Workbooks \
  --input-format pdf \
  --output tf/burns-workbooks
```

`convert` is deprecated and prints an explicit diagnostic directing users to
`module`. It still produces the historical standalone graph: `record` slots,
`worksheet` / `section` / `entry` section nodes, all Workbook columns as
features, `otype.tf`, `oslots.tf`, `otext.tf`, and `conversion-report.json`.
Its removal/version boundary is tracked separately so existing scripts are not
silently broken by this migration.

The legacy corpus' narrow CUC interoperability fields (`cuc_tablet` and
`language`) do not make it a CUC extension: it does not contain CUC diplomatic
`sign`, `word`, `line`, or `column` structure.

### Agora status

`agora.materializer.json` currently retains the two legacy user-local,
network-denied single-input materializers:

- `burns-workbooks-csv-text-fabric`
- `burns-workbooks-pdf-text-fabric`

This is the currently supported Agora registration, not the local module's
architecture. The public `module` CLI already materializes the reviewed
CUC-aligned Burns feature module, and Context-Fabric/cfabric-mcp can load that
module together with the exact CUC base as separate ordered locations.

Registering that module as an Agora materializer would require two independent
runtime inputs: the user-local Burns source and an exact acquired CUC parent
resource. The parent-resource execution capability tracked in
`alexsosn/Agora#135` was **closed as not planned / deferred from the current
Agora scope**. Therefore the Burns migration tracker #29 is blocked on a future
Agora scope/capability change rather than on missing local converter support.

This repository does **not** advertise a fake one-input Agora module
materializer, copy CUC into Burns output, or enable an implicit network
fallback. The public `module` CLI is the truthful local materialization path.

### Appendix scope

`output/appendix.csv` has a different 11-column KTU catalogue schema. It is
explicitly excluded from the Workbooks materializer; Appendix → TF needs its own
graph/materializer design rather than being coerced into either the Burns
annotation module or the legacy row model.

## License and attribution

### Software license

The software source code in this repository is licensed under the **MIT License**.
See [`LICENSE`](LICENSE). This MIT license applies to the repository software;
it does not relicense the Burns source material, generated Burns-derived data,
or the external CUC corpus.

### Burns source material and generated artifacts

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

The reviewed Copenhagen Ugaritic Corpus (CUC) base is an external dependency
and is not redistributed by this repository; its upstream license remains
separate from both this software license and the Burns source terms.
