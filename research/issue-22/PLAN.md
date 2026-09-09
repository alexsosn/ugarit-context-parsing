# Plan: normalized Burns source records and stable annotation IDs (#22)

## Preconditions

- Parent architecture branch head: `e08cc75938d64242a4d92741b275311278a3b327`.
- Research for this slice: `research/issue-22/RESEARCH.md`.
- No reference parsing, CUC loading/alignment, TF module writing, or current standalone materializer changes belong in this ticket.
- No Burns-derived PDF/CSV/TF artifact may be committed or uploaded.

## Product boundary

Implement one pure source-domain transformation:

`ordered WorkbookRecord values -> NormalizedBurnsSource(records, annotations)`

`records` preserves every source row. `annotations` groups only contiguous merged-cell textual runs and points back to their ordered row IDs.

The current CSV/PDF loaders remain the authority for extraction and validation. The current graph/writer/CLI continue consuming `WorkbookSource.records` exactly as before.

## Step 1 — RED: identity/path/workbook contract

Add `tests/test_burns_annotations.py` before production implementation. The first RED imports the planned module/types and therefore fails because `ugarit_context_parsing.annotations` does not yet exist.

Synthetic tests must establish:

### Canonical worksheet identity

- equivalent `.csv` and `.pdf` relative paths produce the same extensionless worksheet ID;
- raw source paths remain distinct/verbatim on normalized records;
- absolute paths, traversal components, unsupported suffixes, missing workbook level, invalid workbook number, and missing/out-of-range worksheet number fail closed.

### Workbook/worksheet provenance

- workbook ordinal 1–9 comes from the leading directory ordinal;
- the full workbook directory label remains verbatim provenance;
- worksheet roles map exactly:
  - 1 `prime_gp`
  - 2 `prime_ph`
  - 3 `derived_common`
  - 4 `derived_gp_only`
  - 5 `derived_ph_only`.

### Stable row identity

- every original `WorkbookRecord` field is retained;
- identical logical records with `.csv` vs `.pdf` raw paths have equal `record_id`;
- changing source row, source page, worksheet identity, or any scholarly/find-spot/comment field changes `record_id`;
- Unicode-equivalent NFC/NFD identity payload values hash identically while the stored model values remain verbatim;
- row IDs have the documented full SHA-256 format;
- duplicate logical source-row IDs in one normalization input fail closed.

## Step 2 — RED: contiguous semantic grouping

Add tests proving:

1. two adjacent records with identical worksheet/section/root/headword/KTU/reference values but different find-spot/comment/page fields become **one** semantic annotation;
2. its member row IDs remain ordered and both row records remain independently accessible;
3. annotation identity uses the first source row and shared textual key;
4. `A, B, A` grouping produces three annotations, with the two `A` annotations receiving distinct IDs;
5. grouping never crosses worksheet boundaries;
6. a changed shared textual field starts a new group;
7. annotation IDs are adapter-neutral across equivalent PDF/CSV records;
8. adding/changing only a member find-spot row does not rename the occurrence if first-row/shared-text identity is unchanged, while the changed row receives a different row ID.

## Step 3 — RED: Burns semantic axes

Synthetic real-shaped paths/sections establish:

- workbook I–IV `Section α` -> `positive_fixed`;
- workbook I–IV `Section β` -> `homograph_excluded`;
- workbook V–IX `Section α1` -> `probable_cultic`;
- workbook V–IX `Section α2` -> `no_secure_cultic`;
- workbook V–IX `Section β` -> `homograph_excluded`;
- unsupported workbook/section pair -> explicit `unsupported`, never a guessed positive status;
- `ktu.startswith("Not attested")` -> `non_textual_not_attested`, otherwise `textual`;
- textual status does not erase semantic status;
- worksheet role is independent of semantic status;
- comments containing `?`, `cf.`, or alternative-looking prose leave automatic interpretive status `unspecified`;
- raw comments remain exact.

## Step 4 — RED: architecture isolation/regression

Require:

- normalized types have no CUC-node/reference-target/alignment fields;
- `normalize_workbook_records()` does not mutate frozen input records;
- calling normalization has no effect on `build_tf_data(source)` output for the current standalone graph;
- existing loaders and current test suite remain otherwise unchanged.

For adapter equivalence, construct matching `WorkbookRecord` tuples directly and, where useful, exercise `load_csv_directory()` plus `load_pdf_directory()` with a legal synthetic parser stub that returns equivalent rows. The production normalization function itself accepts `WorkbookRecord`s only.

## Step 5 — Preserve exact RED evidence

Commit tests without production implementation and create a draft PR. Capture the attested workflow run. RED is accepted only if:

- provenance attestation succeeds;
- pre-existing tests remain green up to the new test module;
- the new tests fail because the planned annotations module/types are absent (or at another explicitly planned missing seam);
- no unrelated failure occurs.

Do not commit GREEN until RED evidence is inspectable.

## Step 6 — GREEN: minimal source-domain implementation

Create `src/ugarit_context_parsing/annotations.py` only. Prefer frozen dataclasses and `str` enums.

Planned API:

- `BurnsNormalizationError`
- `BurnsTextualStatus`
- `BurnsSemanticStatus`
- `BurnsInterpretiveStatus`
- `BurnsWorksheetRole`
- `BurnsSourceRecord`
- `BurnsAnnotation`
- `NormalizedBurnsSource`
- `normalize_workbook_records(records: Iterable[WorkbookRecord]) -> NormalizedBurnsSource`

Internal helpers may include:

- `_worksheet_provenance(source_file)`
- `_canonical_identity_bytes(payload)`
- `_stable_id(prefix, payload)`
- `_semantic_status(workbook_number, section)`
- `_textual_status(ktu)`
- contiguous grouping helper.

### Model sketch

`BurnsSourceRecord` retains raw fields plus:

- `record_id`
- `worksheet_id`
- `workbook_number`
- `workbook_label`
- `worksheet_number`
- `worksheet_role`
- `textual_status`
- `semantic_status`
- `interpretive_status`.

`BurnsAnnotation` contains shared source semantics plus:

- `annotation_id`
- workbook/worksheet provenance
- `first_source_row`
- shared `section/root/headword/ktu/references`
- textual/semantic/interpretive statuses
- ordered `record_ids`.

`NormalizedBurnsSource` contains ordered tuples of records and annotations. It may offer an immutable lookup helper only if tests justify it; avoid speculative API surface.

### Canonicalization

- stored strings: unchanged;
- hash-payload strings: NFC copies;
- JSON: `ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")`;
- encoding: UTF-8;
- digest: SHA-256 full lowercase hex;
- prefixes: `burns-record-sha256:` / `burns-annotation-sha256:`.

### Contiguous grouping

Walk normalized row records in supplied order. Group while the shared textual key remains equal. Flush on any key or worksheet change. Never sort, globally deduplicate, or reorder records inside normalization: ordering is already an adapter contract and is itself provenance.

## Step 7 — GREEN test run and exact behavior check

Run the full repository workflow. Required green evidence:

- Python 3.10 / 3.12 / 3.13 suites;
- installed-package verification;
- execution-environment evidence;
- CI provenance attestation;
- existing downstream regression jobs;
- all new normalization tests.

Inspect logs for accidental source leakage or unrelated warnings introduced by this change.

## Step 8 — adversarial review on frozen final head

Freeze the final commit before review. Review independently from the implementation rationale and challenge at least:

1. whether any source row can disappear;
2. whether contiguous grouping can accidentally become global deduplication;
3. whether grouping can cross worksheets;
4. whether find-spot/comment row association is retained;
5. whether PDF/CSV adapter-neutral identity accidentally drops meaningful worksheet provenance;
6. whether any absolute root/tree hash/CUC ID leaks into identity;
7. whether Unicode normalization mutates displayed/source values instead of only canonical hash copies;
8. whether derived semantic status improperly changes source identity;
9. whether unsupported sections are guessed;
10. whether uncertainty is heuristically invented from prose;
11. whether Not-attested records remain categorized yet non-textual;
12. whether standalone graph output or loader behavior changed;
13. whether public APIs expose CUC/alignment assumptions too early.

If review finds a blocker, return to implementation, obtain a fresh exact-head green run, and repeat independent review.

## Completion

Merge #22 only after RED history, GREEN current CI, and frozen-head independent review are all present. Close #22 through the merge. Parent #21 remains open and the next architectural slice is #23.