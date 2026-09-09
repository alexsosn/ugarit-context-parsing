# Research: Burns reference grammar and fingerprinted CUC index (#23)

## Scope

This child follows merged #22 and implements the next source/base boundary for the CUC-aligned Burns architecture. It must do exactly two things:

1. parse Burns' **KTU text number + Column C `(Column and) Line Reference`** into conservative structured locators with explicit status/reason;
2. verify and index the reviewed CUC Text-Fabric base needed by later alignment.

It does **not** choose final CUC anchors, match Burns headwords to `g_cons`, write a Burns TF module, compose Context-Fabric, or change the current standalone materializer. Those belong to #26+.

Parent architecture: `research/issue-21/PLAN.md`, Workstream 2.
Normalized Burns source contract: merged #22 / `ugarit_context_parsing.annotations`.

## Authoritative Burns convention

Duncan Coe Burns, *Contents, texts and contexts: a contextualist approach to the Ugaritic texts and their cultic vocabulary* (University of Sheffield PhD, 2003), chapter 5, describes the database columns. White Rose record:

`https://etheses.whiterose.ac.uk/id/eprint/15038/`

The chapter's Column C description is decisive for the semantic core:

- Column B is the KTU text identification number;
- Column C identifies the lexeme location within that text;
- most Column C values are line numbers;
- **Arabic numerals** are line references;
- **upper-case Roman numerals** give column numbering where applicable.

Therefore the production parser may treat Roman-column/Arabic-line structure as authoritative. Punctuation/list/range semantics need corpus evidence as well and must not be guessed from a permissive substring regex.

## Corrected real-source structural evidence

Temporary source-safe Actions probe `research/issue-23/audit_reference_shapes_and_cuc.py` uses the checksum-pinned Workbooks source, production PDF loader, and production #22 normalization. It emits only aggregate symbols: numbers -> `N`, upper/lower alphabetic non-Roman wording -> `W`, Roman-numeral words -> `R`; no Burns wording/rows are printed or persisted.

The first workflow run (`34356470676`) had a research-only normalization bug: the probe inserted alphabetic `R`/`N` placeholders and then converted all alphabetic tokens to `W`. Its CUC byte fingerprints/structural diagnostics were valid, but its Burns shape counts are **invalid and superseded**.

Corrected run `34356801315` fixed token classification in one pass and is the evidence used below. Standard repository CI on the corrected research head also passed.

Corrected source totals:

- 45 PDFs;
- 13,857 normalized source records;
- 10,419 contiguous semantic annotations;
- 748 non-textual `Not attested` annotations;
- 27 textual annotations with empty Column C;
- 252 distinct non-empty textual structural shapes.

High-frequency shape families establish the first production grammar:

- `N`: 5,268;
- `R.N`: 1,191;
- `N, N`: 990;
- `N, N, N`: 361;
- `R.N; R.N`: 212;
- `R.N, N`: 211;
- `N-N`: 122;
- `R.N, N; R.N`: 65;
- `R.N, N, N`: 51;
- `R.N; R.N, N`: 46;
- `R.N; R.N; R.N`: 32;
- `R.N-N`: 21.

Further low-frequency combinations repeat these same list/range/group structures. There are also explicit uncertainty/prose shapes such as `N?`, `N, N?`, `W W`, `W.N`, mixed `R.N; W.N`, parentheses, and malformed punctuation. Frequency is **not** permission to infer their meaning.

### Conservative grammar consequence

The production grammar should support only fully consumed strings made from the documented/observed structural vocabulary:

- one Arabic line number;
- a comma-separated list of Arabic line numbers;
- an inclusive Arabic line range using the observed hyphen notation;
- mixtures of individual lines/ranges separated by commas;
- an upper-case Roman column followed by `.` and the first Arabic line/range;
- comma continuations after a Roman-qualified first item inherit that explicit column within the same group;
- semicolon separates groups; a new Roman prefix establishes the new group's column;
- wrapped/arbitrary surrounding whitespace around structural tokens may be normalized for parsing only.

Do not accept a prefix and ignore residue. Any prose token, `?`, unsupported punctuation, malformed range, missing line, lower-case/invalid structural ambiguity, or other unconsumed material yields an explicit unsupported/malformed status with **zero parsed line locators**. This is deliberately stricter than the old research regex, which extracted numeric substrings from larger strings.

A bounded range expansion is required for robustness. The previous research prototype used a 200-line maximum span; retain a documented maximum rather than allowing attacker-controlled huge expansion. Reversed ranges fail closed.

## KTU + Column C is one locator parse

Parent Workstream 2 explicitly requires a **tablet-only KTU** case. Therefore parsing must combine the already normalized KTU convention with Column C instead of treating Column C in isolation.

Use existing `normalize_cuc_tablet()` for exact KTU spellings (`N.N`, optional letter suffix, optional `KTU` prefix). The parser retains original KTU/reference strings.

Outcomes:

- non-textual `Not attested` annotation -> `non_textual`, no locators regardless of reference text;
- textual + invalid/unparseable KTU -> `invalid_ktu`, no locators;
- textual + valid KTU + empty Column C -> successful **tablet-only** locator;
- textual + valid KTU + fully supported Column C -> one or more tablet+optional-column+line locators;
- textual + valid KTU + unsupported/malformed Column C -> explicit unresolved parse status/reason, no partial locators.

Whether the normalized tablet actually exists in reviewed CUC is not a syntax question. `out_of_cuc` remains an expected #26 lookup disposition rather than a #23 KTU parse failure.

## Proposed immutable reference model

Minimal concepts:

- `BurnsReferenceStatus`: `parsed`, `non_textual`, `invalid_ktu`, `empty_reference` is **not** an error because it yields tablet-only, plus `unsupported`/`malformed` as needed;
- `BurnsReferenceReason`: machine-readable reason codes such as `none`, `non_textual`, `invalid_ktu`, `unsupported_wording`, `uncertain_marker`, `unsupported_punctuation`, `malformed_structure`, `reversed_range`, `range_too_large`, `duplicate_target`;
- `BurnsTarget`: normalized tablet, optional column, optional line; line `None` is tablet-only;
- `ParsedBurnsReference`: original KTU, original reference, status, reason, ordered target tuple.

Exact enum naming may be refined in PLAN/tests, but status and reason must remain separate and original strings must survive losslessly.

Repeated identical target syntax should not be silently deduplicated. Treat an exact duplicate locator as malformed/ambiguous (or preserve it for #26 to reject); the preferred #23 contract is fail-closed with `duplicate_target` so downstream accounting cannot confuse authored multiplicity with repeated punctuation.

## Reviewed CUC identity

The compatibility base is:

- repository: `DT-UCPH/cuc`;
- reviewed commit: `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- TF directory: `tf/0.2.8`;
- metadata version: `0.2.8`.

Version text alone is insufficient. User-local CUC TF directories may not retain `.git`, while a directory labelled `0.2.8` can still be modified. Verify exact bytes of the files that determine the warp and the index semantics:

| file | size | SHA-256 |
| --- | ---: | --- |
| `otype.tf` | 531 | `d3ab2f599b7a1e1029608670c739b8439986a7be092d5d1b5eac5267a2ad554f` |
| `oslots.tf` | 448752 | `362c5bdd944cc6c2658634b83747f5796e61922bf81164e05ac8ebd579da85c8` |
| `tablet.tf` | 3036 | `db3429847e6daf67dd07452a72615ac999aa4419ea101b1e0312d294ceff05ef` |
| `column.tf` | 1200 | `0485fc45900d039a0227ad6c418530d1dfa373393bb3b5e9f0614066c26aaa17` |
| `line.tf` | 20566 | `a2e8122ffe274ff47b4b1f64f9a54dd623ec57d48bf95f74152bad35fff3fcf8` |
| `g_cons.tf` | 124223 | `7ac1a6a4c2641aa1b2579e8c204fcb93f18f9d6629c950054482cd2983dbcd80` |

Canonical JSON of `{filename: {sha256, size}}`, sorted keys/compact separators, hashes to reviewed required-files manifest SHA-256:

`717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba`

This content fingerprint is the runtime authority. The reviewed repository/commit/version remain provenance metadata recorded alongside it.

`otext.tf` confirms `sectionFeatures=tablet,column,line` and `sectionTypes=tablet,column,line`. It is useful documentation, but the six exact required files above are sufficient to bind the warp (`otype`, `oslots`) and every value used by the #23 index (`tablet`, `column`, `line`, `g_cons`). If later consumers rely on additional base features, that later module compatibility fingerprint may extend this set rather than silently weakening this one.

## CUC structural evidence

Corrected research run against the reviewed bytes observed:

- signs: 146,017 (slot type);
- columns: 334;
- lines: 7,616;
- tablets: **279**;
- words: 27,770;
- duplicate tablet labels: 0;
- duplicate exact `(tablet, column, line)` keys: 0;
- `(tablet, line-number)` keys spanning more than one column: **607**;
- maximum candidate columns for one tablet/line number: **8**;
- word nodes with empty/missing `g_cons`: **528**.

Consequences:

1. Exact line index key is `(tablet, column, line)`.
2. Also build `(tablet, line) -> ordered candidate lines` because Burns often omits column. **Never choose the first candidate.** #26 may use a bare-line target only when lookup is unique or may report ambiguity.
3. Build `(tablet, column) -> column node` and `tablet -> tablet node`; duplicate keys fail closed.
4. Each line carries its ordered word nodes and `g_cons` values for #26. Empty `g_cons` is valid reviewed data and must be preserved, not treated as structural corruption.
5. Expected reviewed type counts are a second semantic sanity check after byte fingerprint verification. A mismatch is a hard compatibility error.

## Fingerprint failure model

Public `build_reviewed_cuc_index(path)` should:

1. require a real local directory;
2. verify all six required files exist as regular files (and reject symlink redirection if following existing source-hardening policy);
3. compute sizes/SHA-256 and compare every required file to the reviewed constants;
4. only then load Text-Fabric features;
5. verify expected type counts and required section structure;
6. build deterministic indexes and fail on duplicate tablet/column/exact-line keys.

The public safe path must not expose `trust_version=True`, `skip_hash=True`, or another convenience bypass. Unit tests may exercise a private pure index-builder seam with synthetic fake APIs; the integration job must exercise the public fingerprinted path against the exact CUC checkout.

## Distribution/licensing boundary

Do not vendor CUC TF files into this repository. CI may check out the reviewed public revision transiently. Fingerprint constants/counts are compatibility metadata, not a copied corpus.

Burns-derived Workbooks rows/references remain local-only under the existing CC BY-NC-ND boundary. Research logs contain only structural symbols/counts; no source wording or generated dataset is committed/uploaded.

## TDD requirements derived from research

### Reference parser RED

Synthetic, non-Burns fixtures must prove:

- valid tablet-only KTU with empty reference;
- Arabic line;
- comma list;
- inclusive range;
- list+range mixture;
- `II.3` style Roman column+line;
- Roman column group with comma continuation inheriting the column;
- semicolon-separated explicit column groups;
- wrapped whitespace;
- non-textual Not-attested disposition;
- invalid KTU;
- prose containing digits does **not** partially parse;
- `?` uncertainty does not partially parse;
- unsupported punctuation does not partially parse;
- reversed/overlarge ranges fail closed;
- duplicate locator fails closed;
- original KTU/reference text remains exact.

### CUC index RED

Synthetic private builder fixtures and a pinned integration job must prove:

- fingerprint mismatch fails before TF indexing;
- missing required file fails;
- exact reviewed manifest matches all six files;
- reviewed type counts are exact;
- tablet index;
- `(tablet,column)` index;
- exact `(tablet,column,line)` index;
- `(tablet,line)` ambiguity multimap retains all candidates deterministically;
- ordered line words/`g_cons`, including empty values;
- duplicate tablet/column/exact-line structural keys fail closed;
- no CUC bytes are written/copied into package output.

## Non-goals

- no lookup of Burns KTU against CUC to decide `out_of_cuc` (#26);
- no reference-to-node resolution (#26);
- no headword matching (#26);
- no Burns TF feature writer (#27);
- no Context-Fabric combined load (#28);
- no Agora migration/deprecation (#29).

## Conclusion

#23 should produce two conservative, independently testable foundations: a fully consuming Burns KTU/Column-C parser that never returns partial guessed locators, and a CUC index that cannot be built from a merely version-labelled but byte-different base. Ambiguity remains data, not an implementation choice.
