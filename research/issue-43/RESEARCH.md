# Research: public CUC-aligned Burns module CLI (#43)

## Scope

#43 is the unblocked producer-side slice of #29. The CUC-aligned feature module implementation is already merged; this ticket exposes it through the public CLI and documentation while retaining the existing standalone row-slot converter as an explicitly deprecated compatibility path.

The final Agora executable migration remains blocked by `alexsosn/Agora#135`: Agora's current materializer plugin schema accepts only `{source}`, `{output}`, and `{source_revision}` placeholders, so it cannot provide both user-local Burns input and an already-acquired CUC parent path. This ticket must not fake that missing runtime capability.

## Current product mismatch

At master `30fa9df80e4fee2d3e49a612c76dc0d3900c946c`:

- `ugarit_context_parsing.cli` exposes only `convert`.
- `convert` loads CSV/PDF Workbook rows, calls the provisional standalone `graph.build_tf_data()`, builds `conversion-report.json`, and writes a complete row-slot corpus with `otype.tf`, `oslots.tf`, and `otext.tf`.
- README presents that standalone corpus as the normal materialization workflow and describes `record` slots / worksheet-section-entry nodes.
- `agora.materializer.json` still advertises only the standalone CSV/PDF materializers and requires warp files in each output.

This public surface is behind the architecture already completed in #21/#27/#28.

## Reusable reviewed module pipeline

The module path does not need new alignment logic. Existing merged APIs provide the complete pipeline:

1. source loaders: `load_csv_directory()` / `load_pdf_directory()` -> Workbook source records;
2. `normalize_workbook_records(records)` -> `NormalizedBurnsSource` with stable source/annotation IDs and worksheet/semantic provenance;
3. `build_reviewed_cuc_index(cuc_path)` -> exact reviewed CUC 0.2.8 identity/index, rejecting missing, symlinked, or fingerprint-mismatched required files;
4. `align_burns_source(source, index)` -> deterministic alignment dispositions/anchors without silent guessing;
5. `build_burns_module(source, alignments, index)` -> six CUC-node feature maps;
6. `build_burns_module_report(...)` -> complete deterministic compatibility/alignment/source accounting;
7. `write_burns_module(...)` -> feature-only output plus `burns-module-report.json`, explicitly forbidding warp/config leakage.

The module metadata is already bound to exact reviewed CUC identity:

- repository `DT-UCPH/cuc`;
- commit `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- TF version `0.2.8`;
- reviewed required-file manifest SHA-256.

## Minimal CLI shape

Use a new subcommand rather than changing the meaning of existing `convert` in place:

```text
ugarit-context-parsing module SOURCE --input-format {csv,pdf} --cuc CUC_TF_DIR --output OUTPUT
```

Rationale:

- keeps the legacy command callable for existing scripts;
- makes the architectural distinction explicit;
- requires the user/host to provide the reviewed CUC base rather than downloading or guessing it;
- works for both CSV and PDF through the same loader -> normalizer -> aligner -> module writer path;
- can later be wired directly to Agora once parent-resource inputs exist.

`--cuc` must be required for module mode. Validation should be delegated to `build_reviewed_cuc_index()` so there is one compatibility authority.

## Failure semantics

Module mode should convert domain validation errors into concise CLI `SystemExit` diagnostics, without tracebacks for expected invalid input:

- Burns source errors: existing `SourceValidationError` -> `source validation failed: ...`;
- normalization errors: `BurnsNormalizationError` -> `Burns normalization failed: ...`;
- CUC identity/index errors: `CucCompatibilityError` -> `CUC validation failed: ...`;
- module/write rejection -> explicit failure diagnostic.

Alignment dispositions such as unresolved/out-of-CUC are reportable domain outcomes, not CLI failures; the writer/report already preserves them.

## Legacy behavior

Keep `convert` functionally unchanged in this ticket, but emit a deterministic deprecation diagnostic to stderr before materialization. The message should point users to `module` and state that `convert` creates the legacy standalone row-slot corpus. Do not use Python `DeprecationWarning`, which is hidden by default and is poor CLI UX.

Removal is separately tracked in #39 so #43 does not smuggle a breaking change into a product migration.

## README migration

README should lead with the CUC-module workflow:

- explain Burns is an annotation module over reviewed CUC, not an independent diplomatic corpus;
- show CSV and PDF `module ... --cuc ... --output ...` commands;
- list the six `burns_*` features and `burns-module-report.json` as feature-only output;
- state that `otype.tf`, `oslots.tf`, `otext.tf`, and CUC diplomatic features are not emitted;
- keep a clearly marked legacy standalone section with `convert` commands and deprecation status;
- keep licensing/local-only restrictions unchanged.

## Agora boundary

Do not add a false module materializer entry to `agora.materializer.json` yet. The current schema cannot provide two independent inputs. The existing standalone entries remain compatibility entries until Agora #135 supplies parent-resource binding; #29 remains open for that final registry/runtime migration.

The README may state this boundary explicitly so users do not infer that current Agora execution already supplies CUC automatically.

## TDD contract

Before production CLI changes, preserve RED tests that require:

1. parser/help exposes `module` with required `--cuc`;
2. module CSV path calls the real normalized/alignment/module pipeline and emits only six feature files + report;
3. PDF path uses the existing PDF loader but the same downstream module pipeline;
4. invalid CUC produces `CUC validation failed` and leaves no output artifact;
5. `convert` still works and emits a stable deprecation message to stderr;
6. module output is composable with the reviewed CUC base without changing its warp/node counts;
7. help/README identify module mode as primary and legacy convert as deprecated.

Use synthetic Burns input only in tests; no Burns-derived fixture may be committed.

## Adversarial review targets

- Did the new command accidentally reimplement alignment instead of composing existing APIs?
- Does PDF mode genuinely use `load_pdf_directory()`?
- Can failed CUC validation leave a partial output directory?
- Are unresolved/out-of-CUC annotations preserved rather than treated as fatal or silently omitted from the report?
- Is any warp/config/CUC feature copied into module output?
- Is legacy `convert` still behaviorally usable apart from stderr diagnostic?
- Does documentation accidentally claim Agora two-input execution before #135 exists?
- Are source/license restrictions unchanged?
