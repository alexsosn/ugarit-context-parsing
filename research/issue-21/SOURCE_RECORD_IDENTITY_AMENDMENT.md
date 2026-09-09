# Research amendment: source-row identity vs Burns annotation identity

The aggregate real-source evidence in `REAL_SOURCE_AMENDMENT.md` establishes that 13,857 parser rows represent 10,415 semantic Burns annotation groups because merged KTU/reference cells can span several find-spot subrows. This requires an explicit two-level identity model before #22 implementation.

## Problem

`WorkbookRecord` is intentionally self-contained: merged PDF cells are forward-filled so every find-spot row repeats the shared `section`, `root`, `headword`, `ktu`, and `references`. Treating every `WorkbookRecord` as a distinct textual annotation would therefore manufacture 3,442 extra occurrence annotations in the current source and inflate downstream CUC multiplicity.

At the same time, globally collapsing equal textual values is unsafe. The same headword/KTU/reference values can occur again later in a worksheet and must remain distinguishable. Comments and find-spot fields also belong to individual source rows and must not be reduced to unordered sets that lose their row association.

## Required two-level model

### Stable source-record identity

Every parsed `WorkbookRecord` remains represented by an immutable normalized source record with its own `record_id`. Its canonical identity includes:

- canonical worksheet identity;
- source row and source page;
- raw section/root/headword/KTU/reference values after the existing parser repairs;
- locus, room, point, depth, disputed flag, and comments.

This is the lossless provenance layer. A change to any of those values changes the row identity.

### Stable semantic annotation identity

A semantic Burns annotation groups a **contiguous run** of normalized source records which share the authored merged-cell textual identity:

- canonical worksheet identity;
- section;
- root;
- headword;
- KTU;
- references.

The annotation stores the ordered tuple of member `record_id` values. Its identity also includes the first source-row position of the contiguous run, so a later identical occurrence in the same worksheet remains a distinct annotation.

Grouping must never be a global dictionary deduplication by field values.

Find-spot/comment/page provenance remains accessible through the ordered member source records rather than being flattened into unordered aggregate sets.

## CSV/PDF equivalence

The canonical worksheet identity is the normalized relative source path **without the adapter extension**. Thus corresponding `.../Worksheet 1.pdf` and `.../Worksheet 1.csv` sources normalize to the same worksheet identity when their parsed records are otherwise equivalent.

Neither `record_id` nor annotation identity may contain the absolute source root or the adapter kind. This makes direct-PDF and generated-CSV materialization converge on the same Burns source identities while retaining relative workbook/worksheet provenance.

## Canonicalization constraints for #22

- Normalize Unicode to NFC for identity serialization; do not case-fold or rewrite scholarly field content.
- Preserve whitespace/punctuation/markers in scholarly fields exactly as emitted by the existing parser/CSV loader; normalization must not silently reinterpret Burns.
- Serialize the versioned identity payload as canonical UTF-8 JSON (`sort_keys=True`, compact separators, `ensure_ascii=False`) and hash with SHA-256.
- Use the full digest in IDs; do not depend on a truncated hash without explicit collision detection.
- Reject malformed source paths (`absolute`, `..`, empty worksheet identity) rather than allowing source-root-dependent IDs.
- Detect duplicate generated IDs within a normalization result and fail closed if different canonical payloads ever map to the same ID.

## Semantic axes are separate from identity layers

Section-derived semantic status is orthogonal to the source-row/annotation distinction:

- Workbooks I-IV: `α -> positive_fixed`, `β -> homograph_excluded`;
- Workbooks V-IX: `α1 -> probable_cultic`, `α2 -> no_secure_cultic`, `β -> homograph_excluded`.

Uncertainty/alternative-reading evidence remains a separate axis and comments remain verbatim provenance. Worksheet role (1–5, prime/derived relationship) is also provenance, not annotation confidence.

Unexpected workbook/section combinations must not be guessed into one of the statuses; #22 must preserve the raw values and expose an explicit unknown/unsupported semantic state or fail closed under a documented contract.

## Boundary

This amendment defines source normalization only. It introduces no CUC node IDs, no reference parsing, no alignment, no TF module writer, and no change to the current standalone graph/materializer output. Those remain later child-ticket responsibilities.