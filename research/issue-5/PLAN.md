# Plan: repeated-run semantic determinism evidence (#5)

## Goal

Provide reproducible, synthetic-data evidence that the real `burns-workbooks-csv-text-fabric` materializer produces semantically equivalent Text-Fabric output when the same source is converted twice under the same resolved runtime environment.

This ticket proves upstream converter behavior. It does not authorize Agora cache reuse by itself; Agora must separately replay the evidence in the exact integrity-verified managed installation and bind any reusable policy to that `execution_identity_sha256`.

## Preconditions

- Research: `research/issue-5/RESEARCH.md`.
- Baseline converter: `e1218b88d9d849c58ee25541339f32b0d8f5a7d3`.
- No Burns-derived source or generated artifact may be committed/uploaded.
- CSV and PDF determinism are separate claims. This slice covers CSV only.

## Semantic comparison contract

The test harness will load each emitted TF artifact through real `tf.fabric.Fabric` and normalize the complete observable converter payload into a deterministic Python structure.

The snapshot must bind:

1. complete node-feature inventory from `Fall()` and every `Fs(feature).items()` mapping, including `otype` and all provenance/domain features;
2. complete edge-feature inventory from `Eall()` and every `Es(feature).items()` mapping, canonicalizing set-like targets and valued-edge mappings without discarding values;
3. content-bearing feature metadata exposed by the loaded TF API, including dataset/config/feature metadata produced by this converter;
4. complete `conversion-report.json` value, because no current converter-owned report field is volatile;
5. section/navigation consequences through the graph/`otext` contract, covered by the complete warp/features plus explicit section-navigation assertions on the richer fixture.

The comparator must not use output directory paths, mtimes, permissions, CLI timing/stdout, or temporary names.

## Synthetic fixture

Construct the source entirely in the test using `WORKBOOK_FIELDS`.

Use at least two worksheet CSV paths and multiple sections/entries so the fixture exercises:

- deterministic normalized file ordering;
- worksheet/section/entry node ordering;
- duplicate section labels and repeated headword/root occurrences that generate `~N` labels;
- Unicode values;
- multiple KTU identifiers plus at least one non-canonical/non-attested value;
- relative `source_file`, `source_row`, and `source_page` provenance;
- CUC identifier normalization;
- conversion report counts/checks.

## RED 1 — repeated-run semantic contract

Commit tests before implementing the semantic snapshot helper.

The RED commit must:

1. create one synthetic source tree;
2. run the real CLI twice into two distinct fresh output directories;
3. require a semantic snapshot for each output and equality between them;
4. require an explicit negative control that changes one semantic value in an in-memory snapshot and proves inequality;
5. require section navigation/labels from both outputs to agree;
6. emit environment evidence to the test log;
7. contain a deliberate unimplemented test-harness snapshot seam so the committed test fails for the intended missing-contract reason, not because converter execution or fixture construction is broken.

Expected RED: the semantic snapshot seam raises `NotImplementedError` after both real conversions complete.

No converter production code changes in RED.

## GREEN 1 — semantic replay helper

Implement only the test-harness semantic snapshot/normalization seam.

Requirements:

- enumerate feature names dynamically (`Fall()` / `Eall()`), not a hard-coded allowlist;
- canonicalize node mappings by integer node id and edge targets deterministically;
- retain edge values when present;
- retain feature metadata needed to distinguish semantically different feature definitions;
- include the full conversion report;
- fail loudly if the TF artifact cannot be loaded;
- do not ignore arbitrary hidden/unknown converter output.

If the two real runs compare equal, make no converter production change.

If they differ, stop GREEN and investigate the first semantic delta. Any converter normalization fix requires a focused new RED regression before production change.

## RED 2 / GREEN 2 — comparator negative controls

The first test already requires a simple negative control. Add focused tests if needed to prove the normalizer detects at least:

- one changed node-feature value;
- one changed edge target/value;
- one changed conversion-report field.

These may mutate copied normalized snapshots rather than generated files; they exist to prove the equality comparator is not vacuous.

## Environment evidence

The replay test must print one canonical JSON record prefixed with `DETERMINISM_ENVIRONMENT=` containing at least:

- Python implementation/version;
- OS/platform/machine;
- sorted resolved installed distributions and versions relevant to the process (recording the full visible distribution set is acceptable and simpler/fail-honest).

Do not upload generated TF directories as CI artifacts. GitHub Actions logs are sufficient upstream evidence; Agora will independently validate/replay inside its managed environment before authorization.

## Test gates

Before final review:

- `python -m unittest discover -s tests -v` on Python 3.10, 3.12, and 3.13 via the ordinary workflow;
- installed-package-outside-checkout gate remains green;
- Agora manifest-contract job remains green;
- exact PR head only;
- no copyrighted source/generated fixture in the diff or workflow artifacts.

## Independent adversarial review focus

Review the frozen final patch without relying on this plan and attempt to falsify the determinism claim:

1. Is every emitted node feature compared, or only named examples?
2. Is every edge target/value compared, including valued edges if introduced later?
3. Can metadata/report drift escape comparison?
4. Does the fixture actually exercise file-order and duplicate-label behavior?
5. Does the negative control prove the comparator sees semantic mutations?
6. Does the test run the real CLI and real Text-Fabric save/reload twice?
7. Are output path/timestamp/mtime differences correctly excluded without blanket ignores?
8. Is environment evidence sufficient to identify the resolved dependency/runtime context?
9. Is CSV evidence accidentally generalized to PDF?
10. Is any Burns-derived restricted content committed, logged, or uploaded?

Every blocking finding becomes a focused RED regression before its fix.

## Definition of done

#5 is complete for the CSV materializer when the exact reviewed PR head passes repeated real synthetic CSV conversion/reload semantic equality on the supported CI Python matrix, the comparator's negative controls pass, environment evidence is present in logs, and a fresh logically independent adversarial review finds no blocking gap.

PDF remains un-attested until an equivalent real-parser synthetic-PDF replay is designed and merged separately.
