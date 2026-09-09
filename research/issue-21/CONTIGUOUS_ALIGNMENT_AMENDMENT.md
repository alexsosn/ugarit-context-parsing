# Research amendment: corrected real-source alignment under contiguous grouping

The independent review of parent #25 found that the first aggregate real-source probe grouped rows globally by scholarly field values. `CONTIGUOUS_GROUPING_AMENDMENT.md` then demonstrated on the checksum-pinned 45 Workbooks PDFs that the correct contiguous authored-run partition contains **10,419** semantic groups, not 10,415.

A second aggregate-only audit reran the Burns→CUC lower-bound analysis using that corrected contiguous partition.

## Evidence identity

- PR: #25
- branch head tested: `46104c871363375dcf50ff4c84b0a20c9b602725`
- workflow: `Burns contiguous alignment audit`
- run: `34340405000`
- reviewed CUC: `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`
- Burns input: repository checksum-pinned `Workbooks.zip`, downloaded only into runner-temporary storage
- privacy guard: no `Workbooks` directory, generated output, or persisted statistics payload remained after the audit
- output: aggregate counts only; no Burns headwords, references, comments, rows, CSV, or TF feature payload was emitted as an artifact

The ordinary repository test workflow on the same head also completed successfully (`34340405088`).

## Corrected source counts

- PDFs: **45**
- raw parser rows: **13,857**
- contiguous semantic annotations: **10,419**
- raw rows absorbed as additional member rows: **3,438**

Semantic status:

- `positive_fixed`: **2,675**
- `probable_cultic`: **1,018**
- `no_secure_cultic`: **2,091**
- `homograph_excluded`: **4,635**

Worksheet roles 1–5:

- 1: **2,595**
- 2: **1,284**
- 3: **3,326**
- 4: **1,458**
- 5: **1,756**

The previous 10,415-based counts in `REAL_SOURCE_AMENDMENT.md` are historical results of the superseded global-dedup heuristic. They must not be used as production acceptance counts.

## Corrected CUC coverage lower bound

Against the reviewed 279-tablet CUC warp:

- in CUC: **5,224**
- `Not attested`: **748**
- out of CUC: **4,362**
- KTU unparsed: **85**

Reference-shape quality under the same conservative research parser:

- simple: **9,550**
- complex: **13**
- empty: **27**
- unparsed: **829**

These remain research lower-bound classifications, not production #23 parser decisions.

## Corrected alignment lower bound

- exact word span, unique: **2,852**
- exact word span, multiple: **1,591**
- line resolved but no exact headword match: **739**
- line unresolved: **21**
- line unresolved because the line number is ambiguous across columns: **5**
- reference unparsed: **16**
- KTU unparsed: **85**
- non-textual `Not attested`: **748**
- out of CUC: **4,362**

Production #26 must still recompute every disposition with its reviewed parser/index rather than importing these heuristic anchors.

## Multiplicity under corrected grouping

All statuses, exact unique candidate alignments only:

- CUC word nodes with any exact annotation: **2,575**
- word nodes with multiple exact annotations: **495**
- maximum annotations on one word: **7**
- overlapping exact annotation pairs: **864**
- nested exact annotation pairs: **864**

Positive `α` + `α1` statuses only:

- CUC word nodes with any positive exact annotation: **1,456**
- word nodes with multiple positive exact annotations: **107**
- maximum positive annotations on one word: **4**
- overlapping positive exact annotation pairs: **120**
- nested positive exact annotation pairs: **120**

The positive-only multiplicity result is unchanged from the earlier heuristic probe and independently confirms that a scalar one-category-per-node representation would be lossy even after excluded/negative statuses are removed.

## Comment evidence

Under corrected grouping:

- annotations with non-empty comments: **2,301**
- heuristic uncertainty signals: **909**
- heuristic cross-reference/alternative signals: **329**

These counts justify preserving comments and keeping interpretive status structurally separate, but they do **not** authorize #22 to infer a structured uncertainty value from prose. The #22 contract therefore keeps automatic interpretive status `unspecified`.

## Supersession rule

Where this amendment and `REAL_SOURCE_AMENDMENT.md` disagree on grouping-dependent counts, **this amendment is authoritative**. The earlier file remains in history to document why the independent review rejected global deduplication.

The architectural conclusions remain unchanged: Burns is a feature-only module over the reviewed CUC warp; source-row and semantic-annotation identities are separate; grouping is contiguous and row-continuity-aware; multiplicity must be lossless; unresolved/out-of-CUC/non-textual cases remain explicitly accounted for rather than guessed into CUC anchors.
