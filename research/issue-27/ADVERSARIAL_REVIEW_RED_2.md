# Second adversarial review RED: Burns TF module (#27)

Reviewed GREEN head: `b94af31f0a6c5e99ed81b4b68c4f72d4d2934816`.

The full Python matrix, installed-package checks, Agora, pinned Context-Fabric consumer, and exact reviewed-CUC composition gate are green on that head. A fresh full-diff review nevertheless found two remaining representation-integrity blockers.

## Finding 1 — authoritative payload placement is not revalidated by the writer

The builder emits a word-span occurrence identically on every node in its complete ordered `anchor_nodes` tuple. The public writer now re-derives projections and validates compatibility metadata, but it still accepts a manually constructed `BurnsModuleData` when:

- an otherwise valid payload is moved to a node not named in its own `anchor_nodes`;
- one participating node copy of a multi-word occurrence is removed; or
- two copies with the same stable occurrence identity disagree in non-identity payload fields.

That violates #27's core representation contract: discovery from any participating word must reconstruct one complete occurrence, and module serialization must not permit wrong-node attachment.

Required writer-side validation, before Fabric construction:

1. every authoritative node key is a positive integer;
2. every payload's `anchor_nodes` is non-empty, positive, duplicate-free, and includes the node carrying that payload;
3. `tablet`/`line` payloads have exactly one anchor node; `word_span` payloads use the complete ordered anchor tuple;
4. all copies sharing one stable occurrence identity are byte/canonically identical;
5. the set of nodes carrying an occurrence is exactly the set named by its `anchor_nodes`.

This validates module self-consistency. Scholarly correctness against CUC remains the responsibility of `build_burns_module()` / #26 alignment validation.

## Finding 2 — unanchored records lose normalized Burns metadata in materialized output

Parent #21 requires Burns contextual/findspot/comments/provenance to remain available and explicitly requires out-of-CUC/unresolved source records to remain represented in the alignment report. #27's node payload preserves full row-specific metadata only for selected anchors. The embedded #26 alignment report retains only `record_id`, source file/row/page plus reference/alignment details; it does not retain section/root/headword, worksheet taxonomy, semantic statuses, locus/room/point/depth/disputed/comments for an unanchored record.

Required module-report fix: add a deterministic top-level `source_records` inventory containing every normalized `BurnsSourceRecord` field, with enum values serialized as strings. The embedded alignment report continues to map annotations/dispositions to those stable record IDs.

The writer should at minimum verify report/source-record count and ID partition consistency that can be checked without the original source object.

## Preserved RED

Before production changes add synthetic tests requiring:

- wrong-node authoritative placement is rejected before Fabric construction;
- a missing copy of a multi-word span is rejected before Fabric construction;
- divergent copies sharing one occurrence identity are rejected before Fabric construction;
- a fully unresolved annotation still has every normalized source-record field available from `burns-module-report.json` data.

After RED, make only the narrow validator/report changes, strengthen the real reviewed-CUC gate to exercise a line anchor as well as tablet/single-word/multi-word cases, then rerun all exact-head gates and restart adversarial review.