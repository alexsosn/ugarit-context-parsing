# Plan: pure Burns→CUC alignment and deterministic accounting (#26)

## Preconditions

- Parent architecture #21 remains open.
- #22 normalized Burns source/annotation model is merged.
- #23 conservative reference parser and fingerprinted reviewed-CUC index are merged.
- Research for this slice is `research/issue-26/RESEARCH.md`.
- No Burns-derived source rows, alignment payload, or CUC corpus files may be committed/uploaded.
- No Text-Fabric writer, new TF nodes, combined consumer work, or legacy deprecation belongs here.

## Production seam

Add `src/ugarit_context_parsing/alignment.py` as a pure layer over:

- `BurnsAnnotation` / `NormalizedBurnsSource` from `annotations.py`;
- `parse_burns_reference()` / `BurnsTarget` from `references.py`;
- immutable `ReviewedCucIndex` from `cuc_index.py`.

The alignment layer must not load Text-Fabric, read PDFs/CSVs, or write module features.

## Public immutable model

Freeze these enum concepts in RED before production exists.

### `BurnsAlignmentDisposition`

- `aligned`
- `ambiguous`
- `partial`
- `unresolved_reference`
- `out_of_cuc`
- `non_textual`

### `BurnsAlignmentReason`

At minimum:

- `none`
- `non_textual`
- `tablet_not_in_cuc`
- `reference_parse_failed`
- `line_not_found`
- `ambiguous_line`
- `headword_not_found`
- `empty_headword`
- `ambiguous_headword_span`
- `mixed_target_results`

The full #23 parse status/reason remains available through the embedded `ParsedBurnsReference`; do not duplicate every parse reason into alignment enums.

### `BurnsAlignmentConfidence`

Evidence classes, not probabilities:

- `exact_lexical`
- `exact_structural`
- `none`

### `BurnsAnchorKind`

- `tablet`
- `line`
- `word_span`

### `BurnsAlignmentOccurrence`

Immutable fields:

- deterministic `occurrence_id`;
- zero-based `target_ordinal`;
- original structured `BurnsTarget`;
- occurrence disposition/reason/confidence;
- selected `anchor_kind` or `None`;
- selected ordered `anchor_nodes` tuple;
- `context_line_node` for line/word-span occurrences;
- ordered `candidate_line_nodes` for structural ambiguity;
- ordered `candidate_spans` for lexical ambiguity.

Exactly one occurrence result is produced per parsed target.

### `BurnsAnnotationAlignment`

Immutable fields:

- `annotation_id`;
- ordered `record_ids` copied from #22 semantic annotation identity;
- embedded `ParsedBurnsReference`;
- annotation-level disposition/reason;
- ordered occurrence tuple.

No source-field mutation and no TF-writing fields.

## Stable occurrence identity

Use canonical JSON + NFC + full SHA-256, prefix `burns-occurrence-sha256:`.

Identity payload:

- schema `burns-alignment-occurrence-v1`;
- `annotation_id`;
- `target_ordinal`;
- canonical target `tablet`, `column`, `line`.

The occurrence ID is independent of absolute source roots and does not depend on iteration order outside the authored target ordinal.

## Reference/structural resolution

`align_burns_annotation(annotation, index)`:

1. call #23 `parse_burns_reference()` exactly once;
2. non-textual parse result -> annotation `non_textual`, no occurrences;
3. any non-`parsed` textual result -> `unresolved_reference`, reason `reference_parse_failed`, no occurrences;
4. if parsed tablet is absent from `index.tablet_nodes` -> `out_of_cuc`, no occurrences;
5. otherwise resolve each target in order.

### Tablet-only target

Select tablet node:

- disposition `aligned`;
- reason `none`;
- confidence `exact_structural`;
- anchor kind `tablet`;
- one anchor node.

### Explicit column line

Lookup exact `line_nodes[(tablet,column,line)]` only.

- found -> continue to lexical narrowing;
- absent -> `unresolved_reference` occurrence, `line_not_found`, no selected anchor.

### Bare line

Lookup `bare_line_candidates[(tablet,line)]`.

- zero -> unresolved occurrence / `line_not_found`;
- one -> continue to lexical narrowing;
- more than one -> `ambiguous` occurrence / `ambiguous_line`, no selected anchor, all candidate lines retained.

Never first-hit a candidate list.

## Conservative lexical narrowing

Normalize the Burns headword only for matching:

1. NFC;
2. split on whitespace;
3. strip trailing `*†!?` from each token;
4. drop only tokens made empty by that documented suffix stripping;
5. exact case-sensitive comparison to NFC CUC `g_cons`.

Do not modify the stored source headword.

For one exact line:

- unique contiguous span -> `aligned`, `exact_lexical`, `word_span`, complete ordered word tuple;
- no span -> `aligned`, `headword_not_found`, `exact_structural`, safe line anchor;
- headword becomes empty -> `aligned`, `empty_headword`, `exact_structural`, safe line anchor;
- multiple contiguous spans -> `ambiguous`, `ambiguous_headword_span`, `exact_structural`, safe line anchor plus all candidate word spans.

An in-order but discontinuous token sequence is not a word span and therefore takes the no-span line fallback.

Empty CUC `g_cons` remains a real word value and is not skipped.

## Annotation-level summary

For parsed in-CUC annotations with occurrences:

- all occurrence dispositions `aligned` -> annotation `aligned`, reason `none`;
- all `ambiguous` -> annotation `ambiguous`; if all reasons equal use that reason, otherwise `mixed_target_results`;
- all `unresolved_reference` -> annotation `unresolved_reference`; same reason-fold rule;
- any mixture of aligned/ambiguous/unresolved -> annotation `partial`, reason `mixed_target_results`.

Successful sibling occurrences survive a partial annotation.

## Source-level alignment

`align_burns_source(source, index)`:

- validate unique annotation IDs;
- preserve normalized semantic annotation order;
- align each annotation exactly once;
- return an immutable tuple.

Nested/overlapping annotations are independent calls. No global node/span/category deduplication occurs.

## Deterministic report

Add:

- `build_alignment_report(source, alignments, index) -> dict[str, object]`;
- `alignment_report_json(source, alignments, index) -> str`.

Validation before serialization:

- source annotation IDs unique;
- supplied alignment IDs unique;
- alignment ID set equals source annotation ID set exactly;
- each annotation alignment `record_ids` equals the source annotation's ordered record IDs;
- every record ID resolves to exactly one `BurnsSourceRecord`;
- reject inconsistent accounting instead of filling/omitting entries silently.

Report schema `burns-cuc-alignment-report-v1` contains:

- record/annotation totals;
- sorted disposition counts;
- reviewed CUC compatibility metadata when present;
- one annotation entry per semantic annotation, ordered by `(worksheet_id, first_source_row, annotation_id)`;
- annotation ID + ordered record IDs;
- ordered source provenance (`record_id`, relative `source_file`, `source_row`, `source_page`);
- original KTU/reference strings;
- parser status/reason/targets;
- disposition/reason;
- complete ordered occurrence payload including ambiguity candidates.

Serialize JSON with UTF-8 logical text, `sort_keys=True`, compact separators, no absolute source root.

## User-local audit command

Add `scripts/audit_burns_alignment.py` after core GREEN.

Inputs:

- `--cuc PATH` required reviewed CUC TF directory;
- optional `--workbooks PATH`; if absent use checksum-pinned `ensure(WORKBOOKS)`;
- optional `--report PATH` writes the full local alignment report.

Default stdout is aggregate-only:

- source file/record/annotation counts;
- annotation disposition counts;
- occurrence disposition/reason/anchor-kind counts;
- word-span length histogram;
- number of CUC nodes participating in multiple selected Burns anchors and maximum multiplicity.

Never print Burns strings/rows/comments/headwords/references in aggregate mode.

## Preserved RED gate

Create tests before `alignment.py` exists.

### Core alignment RED

Synthetic fixtures prove:

1. non-textual -> no anchors;
2. valid parsed tablet absent from CUC -> out-of-CUC;
3. malformed/unsupported reference -> unresolved parse with embedded #23 reason;
4. tablet-only exact anchor;
5. explicit column+line exact structural anchor;
6. bare line unique resolution;
7. bare line ambiguity preserves every candidate and selects none;
8. missing line selects nothing;
9. unique one-word `g_cons` match -> one-node `word_span`;
10. unique contiguous multi-word headword -> one occurrence with ordered full span;
11. repeated matching token/span -> lexical ambiguity, all candidate spans retained, safe line anchor selected;
12. discontinuous token sequence is not accepted as a span;
13. trailing documented editorial markers do not block exact lexical match;
14. arbitrary punctuation is not stripped to manufacture a match;
15. empty headword -> safe line anchor;
16. zero lexical match -> safe line anchor;
17. multiple parsed targets produce ordered occurrences and stable IDs;
18. mixed resolved/unresolved targets -> `partial` while retaining successful anchors;
19. two annotations may select identical/nested/overlapping word nodes without merge;
20. repeated call yields identical immutable results.

### Report RED

Synthetic normalized source proves:

- every annotation appears exactly once;
- report uses semantic annotation IDs, not source-row IDs as top-level units;
- ordered `record_ids` and file/row/page provenance survive;
- multi-word span remains one occurrence with full tuple;
- overlapping annotations remain distinct;
- deterministic repeated JSON equality;
- compatibility fingerprint appears when provided;
- duplicate alignment IDs fail;
- missing/extra alignment IDs fail;
- changed/missing record provenance fails;
- no source root path is serialized.

The initial RED is valid only if failures are caused by the missing production alignment module/API while existing tests remain healthy.

## GREEN gate

Implement only:

- `alignment.py` immutable model + pure aligner + report builder;
- later, user-local aggregate audit script.

No TF writer/module output.

Run Python 3.10/3.12/3.13 plus existing Agora/Context-Fabric gates.

After core synthetic GREEN, add/extend a pinned reviewed-CUC integration gate that constructs a legal synthetic Burns annotation against the real public CUC index and proves the production aligner consumes the public verified index without changing it.

## Adversarial review

Freeze an exact final head and independently challenge:

- any path that first-hits bare-line or lexical candidates;
- cross-line/discontinuous/fuzzy lexical matching;
- editorial-marker normalization widening beyond the documented suffix set;
- loss of successful sibling occurrences in partial alignment;
- annotation-vs-source-row accounting confusion;
- overlapping/nested span deduplication;
- unstable occurrence IDs/order;
- mutable result containers;
- report omission/duplication or absolute-path leakage;
- accidental TF writer/warp/module changes;
- real reviewed-CUC compatibility behavior.

Only then mark ready and merge.
