# Research: feature-only Burns TF module over CUC (#27)

## Preconditions

- Parent architecture #21 is merged.
- Source identities #22, reviewed CUC/reference index #23, and Burns→CUC alignment #26 are merged.
- Base for this slice: `master@2c2301352c4f10a03914ef1e14f2fd632ce59a14`.
- Reviewed CUC remains `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF 0.2.8; the exact warp, including 279 tablet nodes, is authoritative.

## Existing seams

`alignment.py` already produces immutable `BurnsAlignmentOccurrence` objects. An occurrence has a stable `occurrence_id`, disposition, anchor kind, complete ordered `anchor_nodes`, context line, and candidate evidence. `BurnsAnnotationAlignment` retains the semantic annotation ID and ordered source-record IDs.

The existing `writer.py` is intentionally the standalone-corpus writer. It requires `otype.tf`, `oslots.tf`, and `otext.tf` and transactionally publishes them with `conversion-report.json`. Reusing that contract for a module would be wrong: a Burns module must own no warp.

Text-Fabric feature modules are feature wefts around an existing base warp. The writer should therefore call `Fabric.save(nodeFeatures=..., edgeFeatures={}, metaData=..., location=<stage>, module="", ...)` with Burns node features only, then explicitly reject any staged `otype.tf` or `oslots.tf`. Combined validation loads the reviewed CUC base and the Burns feature directory together; the base supplies warp and section structure.

## Authoritative representation

The authoritative node feature is `burns_annotations`. Its value is a deterministic compact JSON array string. Each entry represents one aligned occurrence and contains enough identity to reconstruct it without annotation nodes:

- schema/version;
- `annotation_id`;
- `occurrence_id`;
- ordered `record_ids`;
- disposition/reason/confidence;
- anchor kind;
- complete ordered `anchor_nodes` tuple;
- context line node where applicable;
- source semantic/textual/provenance fields needed by downstream Burns queries.

For a word span, the same canonical occurrence entry is discoverable on every participating existing CUC word, but the complete ordered span remains inside the entry. Consumers deduplicate by `(occurrence_id, anchor_nodes)`, never by headword/category or carrier node.

Tablet and line anchors are stored on their corresponding existing CUC nodes. Ambiguous/unresolved/out-of-CUC/non-textual annotations have no authoritative carrier node and remain in the alignment report, not guessed into module features.

Nested and overlapping occurrences are ordinary multiplicity: each carrier node stores a canonically sorted array of all applicable occurrence entries. Exact duplicate occurrence entries are rejected or deterministically deduplicated only when both occurrence identity and full anchor tuple agree.

## Convenience projections

Query-friendly node features may include `burns_present`, `burns_headwords`, `burns_semantic_statuses`, `burns_sections`, `burns_workbooks`, and `burns_anchor_kinds`. They are deterministic projections from `burns_annotations`, never independent truth. Multi-valued projections require a documented canonical separator/encoding and must survive punctuation/Unicode without ambiguity; JSON arrays are safer than delimiter-joined strings where values are unrestricted.

## Metadata / compatibility

Every Burns feature file must identify the module and reviewed CUC compatibility boundary. Metadata should include at least `coreData=CUC`, `coreVersion=0.2.8`, Burns module schema/version, reviewed CUC repository/commit, and a stable compatibility fingerprint derived from the exact reviewed warp/index identity already enforced by #23.

The module must not copy CUC diplomatic features (`g_cons`, `tablet`, `column`, `line`, etc.) merely to make standalone loading possible. Base-only CUC remains valid; Burns module loading without its compatible CUC base is not a supported corpus.

## Publication

Module files plus `alignment-report.json` form one publication unit. Stage in a sibling temporary directory, validate staged contents, then replace the destination transactionally with rollback. A failed `Fabric.save`, unexpected warp file, report validation failure, or publication exception must leave the previous complete module/report intact.

No Burns source PDF/CSV or generated real-source TF module may be committed/uploaded. Real-source checks may use runner-temporary storage and aggregate-only evidence.

## Combined-load invariants

A test against the exact reviewed CUC base must establish before/after invariants:

- slot type remains `sign`;
- max slot/max node and node-type counts are unchanged;
- base feature values are unchanged;
- Burns features appear only on existing node IDs;
- two annotations on one node survive;
- one multi-word occurrence is reconstructable as one occurrence from all carrier words;
- nested/overlapping spans survive without overwrite;
- Unicode/newline/punctuation in JSON payload survives TF save/reload exactly.

## Main adversarial risks

1. `Fabric.save` may emit assumptions from the standalone writer if given warp metadata incorrectly; staged file inventory must be asserted.
2. Scalar TF node features can overwrite multiplicity unless values are assembled per node before save.
3. Replicating a span payload to carrier words can look like duplicate annotations unless full span identity is embedded and consumer reconstruction is tested.
4. Convenience projections can become a second inconsistent truth unless derived from the authoritative payload in one code path.
5. A writer that copies CUC warp/features to make tests easy would recreate the architecture #21 explicitly rejected.
6. Publication of module files and report separately can expose mismatched generations after failure; transactional rollback is required.

## Scope

This ticket ends at a supported feature-only TF module plus direct Text-Fabric combined-load proof. It does not change Context-Fabric/cfabric-mcp composition (#28), Agora/product registration or legacy deprecation (#29), or software licensing/release policy (#15/#16).