# Plan: conservative Burns reference grammar and fingerprinted CUC index (#23)

## Preconditions

- Parent architecture #21 is merged.
- Source-domain normalization #22 is merged and is the only Burns semantic-input boundary used here.
- Reviewed CUC base is exactly `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`.
- Research evidence is `research/issue-23/RESEARCH.md`; corrected source-safe audit run `34356801315` supersedes the earlier shape-classification run.
- No Burns-derived row/reference/headword/comment data and no CUC corpus files may be committed.
- This slice does not select final CUC anchors, match headwords, write TF modules, or alter the standalone materializer.

## Deliverables

Implement two independent production foundations:

1. `ugarit_context_parsing.references`: a fully-consuming parser for normalized Burns KTU + Column C reference strings.
2. `ugarit_context_parsing.cuc_index`: exact-byte verification and deterministic structural indexing of the reviewed CUC base.

The modules may share immutable value types only where that reduces duplication without coupling syntax parsing to a particular local CUC checkout.

## Workstream A — reference parser

### Public model

Introduce immutable types equivalent to:

- `BurnsReferenceStatus`: `parsed`, `non_textual`, `invalid_ktu`, `unsupported`, `malformed`.
- `BurnsReferenceReason`: explicit machine-readable reason values including `none`, `non_textual`, `invalid_ktu`, `unsupported_wording`, `uncertain_marker`, `unsupported_punctuation`, `malformed_structure`, `reversed_range`, `range_too_large`, `duplicate_target`.
- `BurnsTarget(tablet, column, line)` where `line=None` means tablet-only and `column=None` means an unqualified line.
- `ParsedBurnsReference(original_ktu, original_reference, status, reason, targets)`.

Exact enum spellings are fixed by the RED tests before implementation.

### Grammar

The parser must be anchored/full-consumption only. Supported syntax:

- valid KTU + empty reference -> one tablet-only target;
- one Arabic line number;
- comma list of line numbers;
- inclusive `-` line range;
- comma mixture of individual lines/ranges;
- uppercase Roman column followed by `.` and a line/range;
- comma continuations inherit the explicit Roman column inside the same group;
- `;` starts a new group, which may establish a new Roman column;
- surrounding/inter-token whitespace may be ignored for parsing only.

The parser must reject without partial targets:

- prose containing digits;
- `?` uncertainty markers;
- unsupported punctuation or separators;
- lowercase/malformed Roman qualification;
- malformed/reversed/overlarge ranges;
- duplicate resulting targets;
- invalid KTU.

`BurnsTextualStatus.NON_TEXTUAL_NOT_ATTESTED` short-circuits to `non_textual` regardless of the reference string.

Do not infer CUC membership here. A syntactically valid tablet that is absent from CUC remains `parsed`; #26 will classify `out_of_cuc`.

### Range bound

Use a named production constant `MAX_REFERENCE_RANGE_SPAN = 200`, interpreted as `end - start <= 200`. Tests pin the boundary and its failure reason.

## Workstream B — reviewed CUC verifier/index

### Compatibility constants

Production code records:

- repo `DT-UCPH/cuc`;
- commit `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- version `0.2.8`;
- exact required file names, byte sizes, SHA-256 values from RESEARCH;
- expected node-type counts: sign 146017, column 334, line 7616, tablet 279, word 27770;
- required Text-Fabric section types/features `tablet,column,line`.

Public runtime authority is content bytes + semantic structural checks, not the directory name or version text alone.

### Verification order

`build_reviewed_cuc_index(path)` must:

1. require an existing real directory;
2. reject required files that are absent, non-regular, or symlinks;
3. read/hash every required file and compare exact size/SHA-256 before Text-Fabric loading;
4. load only after fingerprint success;
5. validate expected type counts and section hierarchy;
6. build deterministic indexes;
7. fail closed on duplicate tablet, `(tablet,column)`, or `(tablet,column,line)` keys.

No public bypass such as `skip_hash`, `trust_version`, or alternate fingerprint is permitted in this ticket.

### Pure builder seam

To make RED/negative controls legal without vendoring CUC, expose a private/internal pure builder taking a minimal Text-Fabric-like API or pre-extracted structural rows. Tests may use this seam to create duplicate/malformed structures. The public function must always perform fingerprint verification before reaching it.

### Index model

Return an immutable `ReviewedCucIndex` containing at least:

- fingerprint/provenance metadata;
- `tablet_nodes: tablet label -> node`;
- `column_nodes: (tablet, column) -> node`;
- `line_nodes: (tablet, column, line) -> node`;
- `bare_line_candidates: (tablet, line) -> ordered tuple[line nodes]`;
- `line_words: line node -> ordered tuple[word nodes]`;
- `word_g_cons: word node -> string`, preserving empty strings.

Later #26 performs uniqueness decisions; #23 only preserves all candidates deterministically.

## RED gate

Add tests before production modules exist.

### Parser RED cases

Use synthetic strings only:

- tablet-only valid KTU;
- single line;
- comma list;
- inclusive range;
- list/range mixture;
- `II.3`;
- `II.3, 4, 6-7` column inheritance;
- `II.3,4; III.1-2` group reset;
- wrapped whitespace;
- KTU with optional `KTU` prefix and supported suffix form inherited from `normalize_cuc_tablet`;
- non-textual Not-attested short-circuit;
- invalid KTU;
- prose-with-digit full rejection;
- `?` full rejection;
- unsupported punctuation full rejection;
- malformed Roman/line structures;
- reversed range;
- exact maximum range boundary and over-limit range;
- duplicate target rejection;
- exact preservation of original strings.

### CUC index RED cases

Synthetic private-builder fixtures:

- tablet/column/exact-line indexes;
- bare-line multimap with two or more columns retained in deterministic order;
- line -> ordered words;
- empty `g_cons` preserved;
- duplicate tablet fails;
- duplicate `(tablet,column)` fails;
- duplicate `(tablet,column,line)` fails;
- unexpected type count fails at semantic verification seam.

Public-path negative controls:

- missing required file;
- symlinked required file;
- one-byte fingerprint perturbation fails before TF load.

Pinned integration workflow:

- checkout exact reviewed CUC commit transiently;
- invoke public `build_reviewed_cuc_index()` against `tf/0.2.8`;
- assert fingerprint manifest and reviewed counts;
- assert known ambiguity exists for bare `(tablet,line)` lookup without exposing/copying corpus bytes.

RED is valid only if existing repository gates pass up to import/expected missing-production seams and the new tests fail for the planned reason.

## GREEN gate

Implement only enough production code to satisfy the frozen RED contract:

- reference immutable models + parser;
- CUC compatibility constants, verifier, immutable index + private builder;
- no alignment engine logic;
- no TF module writer;
- no CLI/product deprecation.

Then run full current standard CI and pinned CUC integration.

## Post-GREEN adversarial review checklist

Freeze one exact head and independently challenge:

1. parser is full-consumption and never returns partial targets from residue;
2. Roman-column inheritance is limited to its group and semicolon behavior is deterministic;
3. range bound cannot allocate unbounded sequences;
4. duplicate target behavior cannot turn authored ambiguity into silent deduplication;
5. invalid KTU and non-textual behavior are separated from CUC membership;
6. public CUC path cannot bypass exact fingerprint verification;
7. symlink/missing/modified files fail before Text-Fabric load;
8. exact reviewed counts and section hierarchy are checked after byte verification;
9. bare-line ambiguity preserves all candidate nodes; no first-hit selection occurs;
10. empty reviewed `g_cons` values survive;
11. no Burns-derived or CUC corpus payload is committed/generated into package outputs;
12. no #26 alignment decision, #27 writer behavior, or legacy-product change leaked into this slice.

If review finds a blocker, preserve a new failing test or research amendment before corrective production changes.

## Finalization

Before merge:

- remove temporary research-only workflow bookkeeping if it is no longer needed for reproducibility;
- keep source-safe research scripts only when they document reproducible evidence without redistributing restricted data;
- require final standard CI on exact frozen head;
- require pinned CUC integration success on that same logical production state;
- submit commit-anchored logically independent adversarial review;
- mark ready and merge with `expected_head_sha`.

Merging #23 closes only this parser/index foundation. Parent #21 remains open and #26 becomes the next implementation dependency.