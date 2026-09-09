# Research: normalize Burns source records and stable annotation identities (#22)

## Scope

This slice creates the source-domain layer needed by the CUC-aligned Burns module. It does **not** parse Burns references, inspect CUC, align to CUC nodes, write Text-Fabric features, or change the current standalone materializer.

The normalization seam is deliberately above `WorkbookRecord`: both `load_csv_directory()` and `load_pdf_directory()` already converge on the same immutable record shape, so the new layer must consume those records rather than duplicating either source adapter.

Parent architecture context:

- `research/issue-21/RESEARCH.md`
- `research/issue-21/REAL_SOURCE_AMENDMENT.md`
- `research/issue-21/SOURCE_RECORD_IDENTITY_AMENDMENT.md`

Parent research head used for this slice: `e08cc75938d64242a4d92741b275311278a3b327`.

## Existing source contract

`WorkbookRecord` currently contains:

- `source_file`
- `source_row`
- `source_page`
- `section`
- `root`
- `headword`
- `ktu`
- `references`
- `locus`
- `room`
- `point`
- `depth`
- `disputed`
- `comments`

The CSV loader reads one-level `*/*.csv` files in stable relative-path order. The PDF loader reads one-level `*/*.pdf` files in the same stable ordering and passes each PDF through the existing real parser. Both assign `source_row` from the emitted data-row order starting at 1. The generated CSV writer writes the PDF parser's rows without inserting extra data rows, so equivalent direct-PDF and generated-CSV inputs have matching row order/page values.

The parser has already performed its documented Unicode transliteration repairs and explicit editorial corrections before a PDF `WorkbookRecord` reaches this layer. CSV materialization receives the corresponding generated values. This normalization layer must not repeat or reinterpret those repairs.

## Why `WorkbookRecord` is not itself the semantic annotation

Burns' PDFs use merged cells. A headword can span several KTU records, and a KTU/reference cell can span several find-spot subrows. The parser intentionally forward-fills those merged values so every `WorkbookRecord` is self-contained.

The aggregate real-source probe processed all 45 checksum-pinned Workbooks PDFs and observed 13,857 parser rows. Its global field-value grouping produced 10,415 groups, with 3,442 rows absorbed as additional find-spot subrows. That result proves that row count and textual-occurrence count differ materially.

However, the probe grouped globally on `(source_file, section, root, headword, ktu, references)`. That is useful aggregate research evidence but is **not** a safe production identity rule: two authored entries later in one worksheet could have identical values and would be silently merged.

Production normalization therefore needs two levels:

1. a lossless normalized **source record** for every `WorkbookRecord`;
2. a semantic **Burns annotation** representing one contiguous authored merged-cell group and retaining the ordered member source-record IDs.

The real-source `10,415` grouping count is a scale/lower-bound observation, not an acceptance target for production grouping.

## Canonical worksheet identity

Raw `source_file` remains verbatim provenance in the normalized source record, but it cannot be the cross-adapter identity because equivalent source paths differ only by `.pdf` versus `.csv`.

Canonical `worksheet_id` is:

1. parse `source_file` as a POSIX relative path;
2. require it to be relative, contain no `.`/`..` path components, and identify a file below a workbook directory;
3. require suffix `.pdf` or `.csv` case-insensitively;
4. remove only that final adapter suffix;
5. preserve every other path component and character exactly;
6. serialize with `/` separators.

Example logical equivalence:

- `01 Workbook I - Divine Names (DNs)/Worksheet 1.pdf`
- `01 Workbook I - Divine Names (DNs)/Worksheet 1.csv`

both map to the same extensionless worksheet identity.

Absolute source roots, `WorkbookSource.root`, tree hashes, and adapter kind do not participate in row or annotation IDs.

The normalized object still retains the raw adapter-specific `source_file` separately for diagnostic provenance.

## Workbook and worksheet provenance

The real source contains nine stable top-level workbook categories whose directory labels begin `01` through `09`; each contains five worksheets. Rather than making display wording part of semantic logic, derive:

- `workbook_number`: the leading integer `01`–`09` of the first worksheet path component;
- `workbook_label`: the full first path component, preserved verbatim;
- `worksheet_number`: `1`–`5` parsed from `Worksheet <n>` in the final extensionless filename stem;
- `worksheet_id`: the full extensionless relative path above.

Malformed or unsupported workbook/worksheet paths fail closed with a normalization error rather than defaulting to a guessed category/role.

Worksheet roles are deterministic provenance:

1. `prime_gp`
2. `prime_ph`
3. `derived_common`
4. `derived_gp_only`
5. `derived_ph_only`

These roles describe Burns' database construction; they are not confidence scores.

## Source-record identity

Introduce an immutable normalized source-record object. It preserves every `WorkbookRecord` field plus derived workbook/worksheet provenance and classification fields.

The stable row identity is derived from a **versioned canonical source payload**, not from a mutable object representation. Identity payload v1 contains:

- schema string/version;
- canonical extensionless `worksheet_id`;
- `source_row`;
- `source_page`;
- `section`;
- `root`;
- `headword`;
- `ktu`;
- `references`;
- `locus`;
- `room`;
- `point`;
- `depth`;
- `disputed`;
- `comments`.

The raw adapter-specific `source_file` is retained on the model but omitted from the hash so CSV/PDF can converge.

Derived fields such as worksheet role, semantic status, or later CUC alignment are omitted from the source identity. A future change in classification code must not pretend the underlying Burns source record changed.

Before serialization, string values are Unicode-normalized to NFC **for the identity payload only**. Model values remain exactly those emitted by `WorkbookRecord`; this layer does not trim, case-fold, collapse whitespace, remove punctuation, strip editorial markers, or rewrite transliteration.

Canonical bytes are UTF-8 JSON with sorted keys, compact separators, and `ensure_ascii=False`. Hash with full SHA-256. Proposed stable form:

`burns-record-sha256:<64 lowercase hex>`

Full digests avoid an unnecessary truncation/collision policy.

Within one normalization result, duplicate row IDs are invalid because a logical worksheet/source-row locator should occur once. Fail closed rather than silently deduplicating malformed input.

## Semantic annotation grouping and identity

A semantic annotation is formed by walking normalized source records **in their supplied stable order** and grouping only a contiguous run with the same authored merged-cell textual key:

- `worksheet_id`
- `section`
- `root`
- `headword`
- `ktu`
- `references`

A key change flushes the current annotation. A worksheet change always flushes it.

Do not globally collect records by equal key. If key `A` occurs, then key `B`, then the exact same key `A` occurs again, these are two different Burns annotations.

The immutable annotation retains:

- `annotation_id`
- canonical workbook/worksheet provenance
- shared `section`, `root`, `headword`, `ktu`, `references`
- source/textual/semantic status
- `first_source_row`
- ordered tuple of member `record_id` values

Location/page/comment details remain associated with the member normalized source records. Do not flatten them into unordered sets in the authoritative model.

Annotation identity payload v1 contains:

- schema string/version;
- `worksheet_id`;
- `first_source_row`;
- shared `section`, `root`, `headword`, `ktu`, `references`.

Use the same NFC + canonical UTF-8 JSON + full SHA-256 scheme, with proposed form:

`burns-annotation-sha256:<64 lowercase hex>`

`first_source_row` is intentionally part of annotation identity: it distinguishes a later authored occurrence whose scholarly text happens to be identical.

Member row IDs are not part of the annotation hash. The annotation identifies the authored occurrence; adding/correcting a find-spot subrow changes its row identity/provenance but should not necessarily rename the textual occurrence when its worksheet locator and shared scholarly identity stay fixed.

## Textual status

Textual status is independent of semantic category. The existing parser treats `ktu` beginning with `Not attested` as a source note without a textual/find-spot anchor.

Use an explicit axis:

- `textual`
- `non_textual_not_attested`

Matching follows the existing source convention (`ktu.startswith("Not attested")`), preserving the raw `ktu` value separately.

A non-textual row may still belong to a semantic category/status; do not erase its Burns classification merely because it has no CUC anchor.

## Burns semantic status

The dissertation/source audit and aggregate real-source run establish a source-defined section mapping. It is independent of CUC alignment:

### Workbooks I–IV

- `Section α` → `positive_fixed`
- `Section β` → `homograph_excluded`

Here β is a graphologically identical form with another lexical meaning; it must not become a positive DN/PN/GN/jargon annotation.

### Workbooks V–IX

- `Section α1` → `probable_cultic`
- `Section α2` → `no_secure_cultic`
- `Section β` → `homograph_excluded`

α2 is the intended lexeme/phrase without secure cultic application; it is not a homograph.

Unexpected workbook/section combinations are not guessed. Represent them explicitly as `unsupported` while retaining the original section, so the source remains accountably normalized and later publication can decide whether to fail closed.

The aggregate run exactly reproduced the expected source categories: 2,675 `positive_fixed`, 1,018 `probable_cultic`, 2,090 `no_secure_cultic`, and 4,632 `homograph_excluded` under its research grouping.

## Interpretive uncertainty / alternatives

Comments are important: the aggregate probe observed 2,299 non-empty comments and heuristic signals consistent with substantial uncertainty and cross-reference/alternative-reading material. But `WorkbookRecord` has no authoritative structured uncertainty field, and punctuation/word-search heuristics would silently turn prose into editorial semantics.

Therefore #22 must **not infer** uncertainty from `?`, `cf.`, comments, or CUC text.

The normalized model should expose a separate interpretive axis with `unspecified` as the only value assigned automatically in this slice, while preserving comments verbatim. The type may reserve explicit future values (for example `uncertain`/`alternative`) only if they are never populated without a later authoritative parser/evidence rule.

This keeps uncertainty structurally separate from homography and α2 without fabricating classifications.

## Multiplicity and overlap boundary

The aggregate CUC probe found real multiplicity and overlap, including positive-only overlap. #22 does not align to CUC and therefore does not encode node/span assumptions. Its responsibility is to ensure source annotations remain independently identifiable and are never deduplicated by headword/category text alone.

Overlapping or nested CUC spans are handled later by #26/#27.

## CSV/PDF equivalence contract

Normalization is a pure transformation from ordered `WorkbookRecord`s. Therefore two adapter outputs that contain equivalent records except for `.csv`/`.pdf` suffixes in `source_file` must produce:

- identical canonical worksheet identities;
- identical row IDs;
- identical annotation IDs;
- identical semantic/textual/workbook/worksheet derived fields;
- adapter-specific raw `source_file` retained separately.

No source adapter needs production changes for this property.

## Collision and malformed-input behavior

Fail closed on:

- absolute or traversal-bearing `source_file`;
- unsupported source suffix;
- missing workbook directory/worksheet filename;
- workbook number outside 1–9;
- worksheet number outside 1–5 or absent;
- `source_row < 1` or `source_page < 1` if callers construct records outside validated loaders;
- duplicate generated `record_id` within one normalization operation;
- a hash/payload registry contradiction if digest generation is ever injectable/tested.

Do not repair malformed source paths in the identity layer.

## Proposed public source-domain types

A minimal implementation can use frozen dataclasses and string enums:

- `BurnsTextualStatus`
- `BurnsSemanticStatus`
- `BurnsInterpretiveStatus`
- `BurnsWorksheetRole`
- `BurnsSourceRecord`
- `BurnsAnnotation`
- `NormalizedBurnsSource` containing ordered `records` and `annotations`
- `BurnsNormalizationError`
- `normalize_workbook_records(records)`

No type in this slice contains a CUC node ID, parsed column/line target, alignment confidence, TF feature map, or module path.

## Required TDD observations

RED tests must prove at least:

1. all `WorkbookRecord` fields survive on row-level normalized records;
2. IDs are invariant to absolute source roots because roots never enter the function;
3. record/annotation ordering is deterministic for stable adapter output and filesystem creation order cannot affect already sorted loaders;
4. `.csv`/`.pdf` equivalents converge on the same logical IDs;
5. source-row/page/path/scholarly field changes affect row identity as specified;
6. adjacent multi-location rows with shared textual key produce one annotation with ordered member IDs;
7. a later identical textual key after an intervening group produces a distinct annotation;
8. Not-attested rows are explicitly non-textual;
9. α/β/α1/α2 mappings are correct by workbook family and unsupported combinations are explicit;
10. worksheet roles 1–5 are exact provenance and independent of semantic status;
11. interpretive status remains `unspecified` even when a comment contains uncertainty-looking punctuation/text;
12. no CUC/alignment fields appear in the model;
13. invoking normalization does not mutate the input records or alter current standalone graph output.

## Non-goals

- no CUC checkout or fingerprint verification (#23);
- no KTU/reference grammar (#23);
- no word/line/span alignment (#26);
- no alignment report (#26);
- no TF module files (#27);
- no Context-Fabric composition (#28);
- no legacy materializer deprecation/migration (#29).

## Conclusion

The stable foundation for the Burns module is a lossless two-level source model: every parsed row remains auditable, while only contiguous merged-cell source groups become semantic Burns annotations. Stable identities are source-based, adapter-neutral, CUC-independent, and conservative about semantics the current source does not structure explicitly.