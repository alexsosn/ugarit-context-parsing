# Research: deterministic Burns→CUC alignment and accounting (#26)

## Scope

This child follows merged #22 (normalized Burns annotations) and #23 (conservative reference parsing + fingerprinted CUC index). It implements only the pure alignment/accounting layer.

Out of scope here:

- Text-Fabric module serialization (#27);
- combined Text-Fabric/Context-Fabric loading (#27/#28);
- legacy/Agora migration (#29);
- modifying CUC or inventing annotation nodes.

The governing architecture remains `research/issue-21/PLAN.md`, Workstream 3.

## Existing authoritative boundaries

### Normalized Burns source (#22)

`BurnsAnnotation` is the semantic unit to align. It has a stable `annotation_id`, ordered `record_ids`, workbook/worksheet/section identity, root, headword, raw KTU/reference strings, and explicit textual/semantic status.

Several adjacent source records may form one semantic annotation when they differ only in find-spot subrows. Alignment therefore runs once per `BurnsAnnotation`, not once per `BurnsSourceRecord`.

`NormalizedBurnsSource.records` retains every source record and its `source_file`, `source_row`, `source_page`, findspot fields and comments. The alignment report can therefore preserve ordered source-record provenance without duplicating those fields into the alignment engine itself.

### Parsed reference contract (#23)

`parse_burns_reference()` is syntax-only and fully consuming. It returns ordered `BurnsTarget` values containing canonical tablet, optional Roman column, and optional line.

Important consequences:

- non-textual `Not attested` is identified before lookup;
- invalid/malformed/unsupported syntax yields zero targets and explicit parse status/reason;
- one empty Column-C reference produces a tablet-only target;
- lists/ranges are already flattened into authored target order;
- duplicate targets fail in the parser rather than being silently deduplicated;
- syntactically valid KTU that is absent from CUC remains syntactically valid.

Alignment must not re-parse or widen that grammar.

### Reviewed CUC index (#23)

`ReviewedCucIndex` is constructed only after exact reviewed CUC 0.2.8 byte/structure verification and exposes immutable deterministic indexes:

- `tablet_nodes[tablet] -> tablet node`;
- `line_nodes[(tablet,column,line)] -> exact line node`;
- `bare_line_candidates[(tablet,line)] -> ordered candidate line nodes`;
- `line_words[line node] -> ordered word nodes`;
- `word_g_cons[word node] -> consonantal transliteration`, preserving empty strings.

The real reviewed CUC contains 607 `(tablet,line)` keys spanning more than one column, with up to eight candidate lines. A bare line number is therefore not globally unique and lookup may never select candidate 0/first-hit.

## Real-source constraints already established for #26

The ticket records aggregate-only real-source research from the checksum-pinned Workbooks and reviewed CUC:

- exact contiguous multi-word headword spans occur;
- at least 120 nested/overlapping positive annotation pairs occur;
- at least 107 CUC words participate in more than one positive Burns annotation;
- a CUC word participates in as many as four positive Burns annotations in that research sample.

These observations are lower bounds, not hard-coded production counts. They establish required representation behavior:

1. one Burns occurrence may anchor an ordered tuple of multiple CUC word nodes;
2. overlapping/nested annotations are independent and must not be merged by node, category, headword or span containment;
3. multiple Burns annotations on one CUC node are normal data, not duplicate errors.

A supplemental aggregate-only workflow on this branch probes alignment shape counts again. Until a run is attested, its output is not used as production evidence.

## Headword/g_cons matching boundary

The Workbook PDF parser already repairs the legacy font to standard Ugaritic Unicode and applies documented editorial headword corrections before `WorkbookRecord` reaches #22.

The same parser explicitly preserves trailing editorial markers `*`, `†`, `!`, `?` on corrected headword tokens. These markers are editorial metadata, not CUC consonants. Therefore word matching may normalize a Burns headword only by:

1. Unicode NFC;
2. splitting on source whitespace into ordered tokens;
3. stripping the documented trailing editorial marker set `*†!?` from each token;
4. comparing the resulting tokens exactly, case-sensitively, to NFC-normalized CUC `g_cons` values.

V1 must **not**:

- case-fold;
- remove arbitrary punctuation;
- substitute the Burns root for the headword;
- skip CUC words with empty `g_cons`;
- perform stemming/morphology/fuzzy/edit-distance matching;
- reorder tokens;
- match tokens across a line boundary.

If conservative exact lexical narrowing fails, the resolved structural line remains the smallest defensible anchor; failure to find a word must not erase a line that Burns explicitly cited.

## Contiguous span semantics

For a uniquely resolved CUC line, compare the normalized Burns headword token tuple against each contiguous window of the line's ordered CUC words.

Outcomes:

- exactly one matching window -> one `word_span` anchor whose authoritative node tuple is that complete ordered window;
- more than one matching window -> lexical ambiguity; do not select one span, but retain the uniquely resolved line as a safe coarse anchor and record candidate spans;
- zero matching windows -> retain the uniquely resolved line as a safe coarse anchor with an explicit lexical-no-match reason;
- empty headword after the documented marker normalization -> line anchor only, explicit empty-headword reason.

A discontinuous in-order token subsequence is **not** an exact word span. It remains line-level unless later research establishes a different scholarly rule.

## Structural target resolution

For each parsed target, in authored order:

### Tablet-only

If the canonical tablet exists, align one exact structural occurrence to the tablet node.

### Explicit column + line

Lookup only the exact `(tablet,column,line)` key.

- one node (the only valid indexed state) -> line is structurally exact;
- absent -> unresolved target; no guessed neighboring line/tablet anchor.

### Bare line

Lookup `(tablet,line)` candidates.

- zero candidates -> unresolved target;
- one candidate -> structurally exact line;
- multiple candidates -> ambiguous target; preserve every candidate line node, select none.

A bare-line ambiguity is different from a lexical ambiguity. In the former the line itself is not known, so there is no safe line anchor. In the latter the line is exact and may safely remain the coarse anchor.

## Annotation vs occurrence vs anchor

The v1 model needs three levels:

1. **annotation** — one stable #22 `annotation_id`, represented exactly once in accounting;
2. **occurrence** — one parsed target position under that annotation, with deterministic occurrence identity and its own status/reason/confidence;
3. **anchor** — zero or one selected safe anchor for that occurrence; a word-span anchor contains one-or-many ordered CUC word nodes.

A multi-line Burns annotation therefore has one annotation result and multiple ordered occurrences. A multi-word expression has one occurrence and one ordered span, not N independent word occurrences.

Recommended deterministic occurrence identity input:

- schema version;
- `annotation_id`;
- zero-based target ordinal;
- canonical target fields (tablet, column, line).

Use full SHA-256 with a human-readable prefix, matching the existing stable-ID style.

## Disposition/status semantics

Annotation-level dispositions should be intentionally small:

- `aligned` — every target has a selected safe anchor and none is structurally ambiguous/unresolved;
- `ambiguous` — all target failures are ambiguity-only and no target is unresolved for a stronger reason;
- `partial` — a multi-target annotation mixes aligned and unresolved/ambiguous target outcomes;
- `unresolved_reference` — reference syntax or every structural target is unresolved;
- `out_of_cuc` — parsed canonical tablet is absent from reviewed CUC;
- `non_textual` — Burns explicitly marks the annotation non-textual.

Occurrence-level reasons carry the detail, including:

- `none`;
- `tablet_not_in_cuc` (annotation-level out-of-CUC; no occurrence anchors);
- `reference_parse_failed` plus preserved #23 parse reason;
- `line_not_found`;
- `ambiguous_line`;
- `headword_not_found`;
- `empty_headword`;
- `ambiguous_headword_span`.

Confidence is not probabilistic. Use evidence classes:

- `exact_lexical` — unique contiguous `g_cons` span on an exact line;
- `exact_structural` — tablet/line is exact but lexical narrowing was unavailable or non-unique;
- `none` — no selected anchor.

For lexical ambiguity on an exact line, the selected safe line anchor has `exact_structural` confidence while candidate word spans remain explicitly unselected.

## Mixed multi-target annotations

Do not make one bad target erase successful siblings.

Each parsed target gets exactly one occurrence result. If target outcomes mix, top-level disposition is `partial`. The report therefore preserves successful anchors while still making incomplete alignment visible.

This is safer than all-or-nothing alignment and preserves Burns's authored multi-line structure.

## Deterministic accounting report

`alignment-report.json` is a local sidecar, not a TF feature file. It must be canonically serializable and contain exactly one top-level entry per normalized semantic annotation.

Each annotation entry records at least:

- annotation ID and ordered source `record_ids`;
- ordered source provenance resolved from `NormalizedBurnsSource.records` (`record_id`, relative source file, row, page);
- original KTU/reference strings;
- #23 parse status/reason and parsed targets;
- annotation-level disposition;
- ordered occurrence records including target ordinal, occurrence ID, status/reason/confidence, anchor kind/nodes, and any ambiguity candidates.

Report-level metadata includes:

- schema version;
- exact reviewed CUC compatibility metadata/manifest fingerprint when available;
- annotation/record counts;
- disposition counts.

Canonical ordering:

- annotation entries by `(worksheet_id, first_source_row, annotation_id)`;
- occurrences by target ordinal;
- candidate line nodes/spans in deterministic node order supplied/derived from the reviewed index;
- JSON with sorted keys and compact separators for deterministic repeated output.

The builder must validate accounting invariants rather than silently repair them:

- duplicate annotation IDs fail;
- every annotation `record_id` must resolve to exactly one normalized source record;
- alignment IDs must cover the normalized annotation set exactly once;
- no absolute source root appears in the report.

## User-local real-source audit

This ticket should include a command/script that:

1. loads locally supplied or checksum-pinned Workbooks using the existing parser;
2. normalizes via #22;
3. verifies/builds the reviewed CUC index via #23;
4. runs the production aligner;
5. prints aggregate-only disposition/anchor/span multiplicity counts by default;
6. optionally writes the full alignment report only to a caller-selected local path.

Normal CI must use synthetic Burns fixtures. A research/integration workflow may transiently download the Workbooks only when logs are aggregate-only and no artifact is uploaded.

## TDD consequences

RED must cover, using synthetic Burns annotations/CUC indexes:

- non-textual annotation;
- syntactically valid out-of-CUC tablet;
- malformed/unsupported reference -> unresolved;
- tablet-only anchor;
- unique explicit line anchor;
- unique bare-line anchor;
- bare-line ambiguity retains candidates and selects none;
- unique one-word lexical span;
- unique contiguous multi-word span;
- repeated same token/span on one line -> lexical ambiguity with safe line fallback;
- discontinuous token sequence does not become a word span;
- empty/unknown headword retains exact line as structural anchor;
- multiple line targets yield ordered independent occurrences;
- mixed resolved/unresolved targets -> `partial` without losing successful anchors;
- nested/overlapping annotations remain separate even on the same word nodes;
- deterministic stable occurrence IDs;
- deterministic report serialization and exact once-only annotation accounting;
- ordered source-record provenance survives report generation;
- duplicate/missing accounting inputs fail closed.

## Conclusion

#26 should produce a pure, deterministic alignment layer that narrows only when CUC structure and exact lexical evidence justify it. Structural certainty is retained when lexical certainty is unavailable; structural ambiguity is never guessed away. The result model preserves annotation identity, multi-target occurrences, ordered word spans, overlap/multiplicity, and complete source accounting for the feature-only writer in #27.
