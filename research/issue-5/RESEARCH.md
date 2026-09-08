# Research: reproducible semantic determinism evidence for Burns materializers (#5)

## Question

What exact upstream evidence is still missing after the CSV repeated-run proof from #3/#4, and what comparison/runtime boundary can Agora rely on without redefining converter semantics downstream?

## Baseline

- `master`: `f271e5697a2dc5c13c783338e2a603ab5434678b`.
- CSV repeated-run evidence is already merged. It uses two distinct absolute source roots, opposite file-creation order, exhaustive generated `.tf` comparison modulo only `@dateWritten=`, complete report equality, and independent Text-Fabric reloads.
- Package runtime contract: Python >=3.10, `text-fabric>=13.1,<14`, `pdfplumber>=0.11`.
- Agora manifest exposes `burns-workbooks-csv-text-fabric` and `burns-workbooks-pdf-text-fabric`.

This issue is therefore not a request to alter scholarly normalization. The remaining CSV gaps are (a) a single explicit semantic comparator that can be negative-tested and (b) exact resolved execution-environment evidence from the CI run used as proof.

## Inputs that can affect semantic output

### CSV materializer

Semantic output is a function of:

1. the set of one-level `*/*.csv` relative paths;
2. the exact bytes of each included CSV;
3. row order within each CSV;
4. parsed field values and Unicode decoding (`utf-8-sig`);
5. converter code, including KTU/CUC identifier normalization and structural-node grouping/allocation;
6. Text-Fabric writer/loader behavior;
7. the resolved Python/dependency/runtime environment insofar as those libraries affect serialization/loading.

The destination path and absolute source-root spelling are intended to be non-semantic. #3/#4 now demonstrates source-root independence and filesystem creation-order independence for the synthetic CSV fixture.

There are currently no CSV CLI options that intentionally change scholarly normalization besides selecting the input format/source and destination.

### PDF materializer

The PDF path has the same graph/report/writer inputs after extraction, plus PDF-specific determinants:

1. the exact PDF relative paths and bytes;
2. `pdfplumber` / `pdfminer.six` extraction behavior;
3. page word geometry, word ordering, and parser thresholds/constants;
4. legacy-transliteration repair and source-specific editorial correction tables;
5. resolved parser dependency versions/platform behavior.

`load_pdf_directory()` sorts PDF relative paths before parsing, and the parser itself explicitly sorts extracted words/coordinates where ordering matters. No random identifiers, clocks, host paths, or unordered-set-derived scholarly values were found in the PDF converter code. That code inspection is not sufficient determinism evidence because `pdfplumber` is an external parser whose output can depend on its resolved dependency closure.

No PDF cacheability claim should follow from this issue unless a legally redistributable synthetic PDF exercises the real packaged parser in repeated runs.

## Scholarly/content-bearing outputs

`write_artifact()` stages and publishes every top-level `*.tf` file produced by Text-Fabric plus `conversion-report.json`.

The semantic comparison surface is therefore:

- exact generated `.tf` filename set;
- all persisted TF feature/config content except explicitly proven volatile metadata;
- loaded node bounds and node types;
- every loaded node-feature name and value for every node;
- every loaded edge-feature name and every forward target/value for every node;
- section/navigation results for all generated non-slot nodes;
- the complete parsed `conversion-report.json`, including source tree hash, source format, counts, converter identity, normalization checks, and status.

Because generated CUC identifiers and ordering-sensitive structural labels are node features, comparing all node-feature values covers them directly. `oslots` and any future edge features are covered both by persisted file comparison and by loaded edge target/value comparison.

## Volatile / non-semantic fields

Text-Fabric 13.x writes `@dateWritten=<current UTC time>` into generated TF files. This wall-clock field is the only currently justified exclusion.

The comparator must:

- remove only lines beginning exactly `@dateWritten=` before byte/text comparison;
- require exactly one such line in every generated `.tf` file on both sides, so the exclusion cannot silently widen or become dead code;
- compare all other TF text exactly, including `@writtenBy`, version metadata, whitespace, ordering, config, feature metadata, and bodies;
- compare `conversion-report.json` with no ignored fields.

Absolute input/output paths and temporary staging paths are not written to the artifact and therefore need no output-field ignore rule.

## Text-Fabric bytewise versus semantic determinism

Raw `.tf` bytes can differ solely because of `@dateWritten`. Under one fixed execution identity, the #3/#4 evidence shows that removing only that line yields identical persisted TF content for the reviewed CSV fixture.

Reload comparison remains necessary even with exhaustive normalized file equality: it proves both artifacts are loadable and gives an explicit semantic contract in terms of nodes/features/edges/navigation rather than making downstream users interpret serialization details themselves.

The existing test compares all loaded node features but only the loaded edge-feature inventory; edge target/value equality is currently inferred from normalized `oslots.tf` equality. #5 should make loaded edge equality explicit so the comparator fully matches the issue contract and remains correct if valued/non-warp edge features are added later.

## Negative-control requirement

The current inline assertions prove equality of two generated outputs but do not prove a reusable comparator rejects a semantic mutation.

A valid negative control should:

1. materialize two equal CSV artifacts through the real CLI/writer;
2. copy one completed artifact to a third directory;
3. make a syntactically valid scholarly mutation in the copy (for example change one canonical `cuc_tablet` value in `cuc_tablet.tf`);
4. show the comparator reports inequality for the perturbed copy while reporting equality for the untouched pair.

The perturbation must happen before the negative artifact is ever loaded, avoiding any possible Text-Fabric cache interaction with an already-loaded path.

## Comparator placement

The comparator is evidence/test-harness logic rather than converter behavior. To keep the package's supported public API narrow, implement it in a private module (`ugarit_context_parsing._semantic_compare`) used by the integration evidence test. Agora should consume the reviewed upstream evidence/test target, not import this private helper as a stable application API.

The comparator should return a deterministic tuple of human-readable difference categories rather than raise on the first mismatch. This supports a meaningful negative-control regression and makes CI failures diagnosable.

## Execution identity and environment evidence

The repository intentionally uses dependency ranges rather than a lockfile. Therefore `master@<sha>` plus Python minor version does not identify an exact dependency closure.

Each successful CI matrix job used as determinism evidence must print a machine-readable environment record after installation and before the replay test, containing at least:

- full Python version and implementation;
- platform/system/release/machine identity;
- the complete resolved installed distribution set (`name==version`, sorted);
- a SHA-256 digest of that canonical environment record.

This log evidence is per CI job. It does not assert that Python 3.10, 3.12, and 3.13 share one closure or that future installs of the same commit resolve identically. Agora must still bind any reusable cache attestation to its own verified managed `execution_identity_sha256` and rerun the upstream evidence in that exact environment.

## TDD gate decision

A real contract gap exists: there is no single comparator with explicit loaded edge target/value equality or negative control. Preserve RED evidence before adding `_semantic_compare.py`:

1. update the integration test to import/use the planned private comparator inside the test;
2. exercise both untouched equality and a perturbed-artifact negative control;
3. run CI at that commit and require failure because the planned comparator module does not yet exist;
4. then add only the helper/workflow evidence needed for GREEN.

The already-merged inline repeated-run assertions remain historical positive evidence; the new RED is for the missing comparator contract, not for a converter nondeterminism bug.

## PDF boundary / follow-up

The repository currently has no legal synthetic PDF fixture that demonstrably exercises the real `pdfplumber` parser through the same source-sensitive table logic. PDF determinism therefore remains unproven and must stay non-reusable in downstream cache policy.

A separate ticket should research the smallest legally generated synthetic PDF that exercises ruled/fallback geometry, row assembly, extraction, transliteration repair, and repeated real-parser materialization without including Burns-derived content.
