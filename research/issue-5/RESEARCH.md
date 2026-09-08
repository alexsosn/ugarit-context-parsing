# Research: repeated-run semantic determinism for Burns materializers (#5)

## Question

What exactly must remain equal across repeated Burns materializer runs before Agora may treat one managed output as reusable for an equivalent request?

## Baseline

Inspected `master` at `e1218b88d9d849c58ee25541339f32b0d8f5a7d3`.

Relevant code/tests:

- `src/ugarit_context_parsing/source.py`
- `src/ugarit_context_parsing/pdf_source.py`
- `src/ugarit_context_parsing/graph.py`
- `src/ugarit_context_parsing/report.py`
- `src/ugarit_context_parsing/writer.py`
- `src/ugarit_context_parsing/cli.py`
- `tests/test_text_fabric_integration.py`
- `tests/test_materialization.py`
- `tests/test_pdf_materialization.py`
- `agora.materializer.json`
- `pyproject.toml`

## Findings

### 1. CSV input discovery and graph construction are structurally deterministic

The CSV loader selects only `*/*.csv` inputs and orders discovered paths by normalized repository-relative POSIX path before reading records. The graph builder enumerates the resulting record sequence deterministically, assigns slot/node IDs in traversal order, constructs worksheet/section/entry nodes in the same sequence, and uses only deterministic counters for duplicate labels.

No wall clock, random generator, process ID, hostname, or ambient network result participates in `build_tf_data()`.

The generated graph metadata is static source/converter metadata. It does not contain a creation timestamp.

### 2. The conversion report is content-derived

`build_conversion_report()` derives its fields from the normalized source and `TFData`:

- converter name/version;
- source format/tree hash/file count;
- record/node/edge and domain-specific counts;
- semantic checks.

The report contains no wall-clock timestamp or random identifier. `writer.py` writes it using `json.dumps(..., sort_keys=True)`, so JSON key order is deterministic as well.

### 3. Text-Fabric bytes are not the right primary determinism contract

`writer.py` delegates `.tf` serialization to the installed Text-Fabric runtime. Even when the in-memory graph is identical, byte-level serialization is an implementation detail of the resolved Text-Fabric version and should not be elevated into the scholarly determinism contract.

Agora already records the exact resolved runtime/dependency environment separately as an execution identity. Reuse should therefore be evidenced within one exact managed execution environment, while semantic equality is established by reloading and comparing the emitted Text-Fabric graph/features.

Byte equality may be measured diagnostically, but semantic replay must not fail solely because a future Text-Fabric serializer changes irrelevant formatting while reloading to the same graph.

### 4. Existing real integration coverage is one-shot

`tests/test_text_fabric_integration.py` constructs a legal synthetic CSV fixture, runs the real CLI once, verifies required files/report, reloads through real `tf.fabric.Fabric`, and checks representative records/section navigation.

That test proves real materialization/loadability but not repeated-run equivalence. There is no current negative control proving a semantic comparator would detect a perturbed output.

### 5. Semantic equality needs to cover the complete TF surface, not a representative subset

A reusable-cache evidence test must compare all scholarly/content state that a downstream Text-Fabric consumer can observe. At minimum:

- node types for every node;
- maximum slot/node and complete node inventory;
- every emitted node feature and all node→value mappings;
- every emitted edge feature and all source→target/value mappings;
- dataset/config metadata exposed by the TF API where stable and content-bearing;
- section hierarchy/navigation implied by `otext` plus graph structure;
- all semantically meaningful `conversion-report.json` fields.

A comparator that checks only a few known features could incorrectly bless nondeterminism in another feature.

### 6. Source provenance values are semantic and must match

Relative `source_file`, `source_row`, `source_page`, source-tree hash, source format, file count, and generated CUC identifier features are part of the output contract. They must be compared, not ignored.

Machine-local absolute source/output paths are not emitted into the TF graph/report and are not part of semantic identity.

### 7. CSV replay can use fully synthetic redistributable data

The existing two-row synthetic fixture is sufficient to exercise:

- hierarchy creation;
- Unicode Ugaritic values;
- multiple KTU identifiers;
- relative source path provenance;
- report generation;
- Text-Fabric save/reload.

For stronger replay evidence, the fixture should include at least two worksheet paths/sections and a duplicate entry/section-label case so ordering and generated `~N` labels are exercised rather than remaining trivial.

No Burns-derived real CSV/PDF data is necessary and none should be committed or uploaded.

### 8. PDF determinism is a separate evidence problem

The PDF materializer invokes the packaged `pdfplumber`-based parser. Its geometry/text extraction is deterministic-looking in source code and source paths are sorted, but real PDF extraction behavior is a dependency/runtime concern. Mocking the parser is insufficient evidence for reusable PDF output.

PDF should remain un-attested until a synthetic PDF fixture can legally exercise the real parser twice under one exact environment and the resulting TF semantics are compared.

CSV evidence must not be generalized to PDF.

### 9. Environment identity must accompany the replay

`pyproject.toml` intentionally allows version ranges (`text-fabric>=13.1,<14`, `pdfplumber>=0.11`, plus a platform-specific `cryptography` bound). Thus the same converter commit can run under different resolved dependency trees.

The upstream test should report reproducible environment information (Python/platform and resolved installed distributions or an equivalent lock/digest). Agora will separately bind reusable authorization to its verified managed `execution_identity_sha256`; this upstream record is evidence, not a substitute for that Agora trust boundary.

### 10. A negative control is required

A semantic comparison helper can accidentally be incomplete or normalize away meaningful changes. Its test suite must deliberately perturb one semantic value/edge/report field and prove comparison fails.

The negative control should mutate only the in-test copy/output; it must not add production nondeterminism.

## Semantic normalization boundary

### Compare

- complete node/edge feature inventories and values;
- node-type/node-count/slot-count identity;
- content-bearing TF/config metadata;
- report converter/source/count/check/status fields;
- relative source provenance and tree hash;
- generated hierarchy labels/identifiers.

### Do not use as semantic equality inputs

- output directory path;
- temporary directory names;
- file mtimes/permissions unrelated to TF semantics;
- stdout timing lines from the CLI;
- future outer Agora provenance such as `created_at` (not emitted by this upstream converter itself).

No current converter-owned report field has been identified as volatile and therefore none should be ignored in v1.

## Implementation direction

1. Add a tests-only semantic snapshot/comparison helper over a real loaded TF artifact plus conversion report.
2. Build a richer synthetic CSV fixture entirely in the test.
3. RED: execute the real CLI twice into distinct fresh outputs and require complete semantic equality plus a negative control; first commit should fail because the helper/replay contract is absent or intentionally asserts the missing test surface.
4. GREEN should preferably be tests/harness only. Change converter production code only if the replay exposes actual nondeterminism.
5. Record environment identity in the CI evidence path without uploading generated TF artifacts.
6. Keep PDF outside the CSV claim until a real synthetic-PDF replay exists.

## Scope boundary

This ticket proves behavior of the upstream converter. It does not add Agora cache semantics, change scholarly normalization, redistribute Burns data, or make a claim about PDF determinism without real-parser evidence.
