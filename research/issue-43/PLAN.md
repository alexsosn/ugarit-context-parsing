# Plan: public CUC-aligned Burns module CLI (#43)

Frozen after `RESEARCH.md`. Production changes must follow the preserved RED and must not widen into Agora runtime/schema work.

## Product contract

Add one primary public command:

```text
ugarit-context-parsing module SOURCE --input-format {csv,pdf} --cuc CUC_TF_DIR --output OUTPUT
```

It must produce only the reviewed Burns feature-module inventory plus `burns-module-report.json`, aligned to the exact reviewed CUC base. Existing `convert` remains available as the deprecated standalone row-slot compatibility command.

## Phase 1 — RED

Add focused CLI tests before changing `src/ugarit_context_parsing/cli.py`.

1. Parser/help exposes `module`, requires `--cuc`, and continues to expose `convert`.
2. CSV module execution uses synthetic Workbook CSV input and a reviewed CUC fixture/path, then requires feature-only output (`FEATURES` + report, no warp/config files).
3. PDF module execution proves the CLI selects `load_pdf_directory()` and then follows the same normalization/alignment/build/write path. The test may mock the PDF loader at the CLI boundary so no new PDF parser fixture is needed here; real PDF parsing already has independent integration coverage.
4. Invalid CUC identity must fail with `CUC validation failed:` before output publication.
5. Legacy `convert` must still succeed on its existing synthetic input and emit a deterministic stderr deprecation diagnostic naming `module` and `standalone`.
6. Help text must call `module` the CUC-aligned feature-module path and `convert` legacy/deprecated.

Preserve the exact failing commit and CI evidence. Expected RED: `module` is not a recognized subcommand and `convert` emits no deprecation diagnostic.

## Phase 2 — GREEN implementation

Change only the minimum producer files needed:

### `src/ugarit_context_parsing/cli.py`

- import existing module pipeline APIs;
- define `module` subparser with `source`, required `--input-format`, required `--cuc`, required `--output`;
- keep `convert` argument contract unchanged;
- factor source loading into one helper shared by both commands;
- for `module`:
  1. load source records;
  2. normalize with `normalize_workbook_records(source.records)`;
  3. build/verify exact reviewed CUC index;
  4. align normalized annotations;
  5. build module;
  6. build module report;
  7. publish with `write_burns_module`;
- translate `SourceValidationError`, `BurnsNormalizationError`, and `CucCompatibilityError` to concise `SystemExit` messages;
- preserve alignment dispositions as report data, not CLI errors;
- print a concise success line identifying files/records/annotations and output path;
- for `convert`, print one deterministic deprecation message to stderr before executing the pre-existing standalone pipeline.

Do not alter `graph.py`, alignment rules, reviewed CUC fingerprints, or module writer semantics unless RED reveals a genuine blocker.

### `README.md`

- replace the primary materialization section with CUC-module usage for CSV and PDF;
- explain exact reviewed CUC requirement and feature-only output;
- enumerate six Burns features + report;
- explicitly state no `otype.tf`/`oslots.tf`/`otext.tf` or copied CUC diplomatic features;
- retain a clearly marked legacy standalone `convert` section and deprecation note;
- explain current Agora limitation and link conceptually to the parent-resource blocker without claiming unsupported execution;
- preserve source/license restrictions.

`agora.materializer.json` remains unchanged in this child ticket because the schema cannot express the required second input. Final migration stays in #29 / Agora#135.

## Phase 3 — tests

Run:

- focused new CLI module/deprecation tests;
- existing module/alignment/index suites;
- full repository test suite on Python 3.10, 3.12, 3.13 through Actions;
- installed-package check;
- Agora manifest validation (must remain backward-compatible while unchanged);
- generic Context-Fabric contract;
- reviewed CUC + Burns Context-Fabric composition contract.

The dedicated CUC+Burns consumer gate must remain GREEN; #43 must not regress the already-reviewed module architecture.

## Phase 4 — exact-head adversarial review

Freeze the final head and review independently of implementation history. Challenge:

- command parsing/backward compatibility;
- use of production normalizer/index/aligner/writer rather than duplicate logic;
- failure atomicity and invalid-CUC behavior;
- feature-only inventory;
- PDF loader routing;
- legacy command usability and visible deprecation;
- README accuracy about Agora limitations;
- unchanged license/local-only boundary;
- exact-head CI provenance.

Any blocking review finding requires a fix and fresh exact-head tests/review. Merge with expected-head protection and close #43 only. #29 remains open pending Agora#135.
