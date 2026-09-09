# Research amendment: aggregate real-source Burns/CUC evidence

The initial parent research recorded that this session could not directly obtain the checksum-pinned Workbooks ZIP and therefore left real-source coverage/multiplicity measurement as a later user-local gate. A closed duplicate research branch (#24) subsequently ran a dedicated GitHub Actions probe which downloaded the repository's checksum-pinned Workbooks source into runner-temporary storage, parsed it, compared it to the reviewed CUC base, emitted aggregate counts/structural shapes only, and asserted that no Burns-derived rows/files/statistics artifact was persisted.

This amendment supersedes the parent statement that no real-source aggregate measurement was available. It does **not** make raw Burns content redistributable and does not authorize committing generated CSV/TF data.

## Probe identity and privacy contract

- Burns source: checksum-pinned `Workbooks.zip` via `scripts/sources.py`.
- Reviewed base: `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`.
- Evidence workflow: closed duplicate PR #24, `Issue 21 real-source research`, run `34338282700`.
- The workflow emitted aggregate counts and structural reference shapes only.
- Its final guard verified that `Workbooks`, generated output, and a persisted statistics payload were absent from the checkout after the probe.

The duplicate branch remains closed; this evidence is carried into canonical parent #25 and its child tickets rather than reviving a second architecture branch.

## Source scale and semantic structure

The 45 Workbooks PDFs yielded:

- 13,857 normalized parser rows;
- 3,442 redundant location rows collapsed into their shared semantic records;
- **10,415 semantic Burns annotations** after that collapse.

Section/status counts:

- `Section α`: 2,675 → `positive_fixed` for Workbooks I–IV;
- `Section α1`: 1,018 → `probable_cultic` for Workbooks V–IX;
- `Section α2`: 2,090 → `no_secure_cultic`;
- `Section β`: 4,632 → `homograph_excluded`.

These counts confirm that semantic status must be explicit and that β/α2 cannot be flattened into a positive boolean category feature.

Worksheet-role counts were 2,594 / 1,283 / 3,326 / 1,458 / 1,754 for roles 1–5 respectively. Prime/derived worksheet role therefore remains first-class provenance rather than being inferred later from aligned CUC nodes.

## CUC coverage and conservative alignment lower bound

Against the reviewed CUC base:

- CUC tablet nodes: **279**;
- Burns annotations with KTU in CUC: 5,222;
- `Not attested`: 748;
- out of CUC: 4,360;
- KTU unparsed: 85.

The aggregate alignment probe found this lower-bound disposition surface:

- exact word-span unique: 2,851;
- exact word-span multiple: 1,590;
- line resolved but no exact headword match: 739;
- line unresolved: 21;
- line unresolved ambiguous: 5;
- reference unparsed: 16;
- KTU unparsed: 85;
- non-textual `Not attested`: 748;
- out of CUC: 4,360.

These are **research lower bounds**, not final production alignment results. The production parser/alignment engine must remain fail-closed and explicitly classify unresolved/ambiguous cases rather than treating the probe's heuristic successes as authoritative anchors.

## Reference grammar evidence

The probe inspected 10,388 non-null reference cells and observed 267 structural shapes. Its source-safe quality classifier reported:

- simple: 9,546;
- complex: 13;
- empty: 27;
- unparsed: 829.

Common shape families include a single line number, Roman-column + line, comma-separated line lists, semicolon-separated column groups, and numeric ranges. #23 must derive a conservative grammar from the demonstrated shape families while preserving original strings and reason codes for unsupported forms; aggregate frequency does not justify guessing ambiguous punctuation semantics.

## Multiplicity/overlap evidence

Across all exact candidate alignments:

- 2,575 CUC word nodes had one exact Burns alignment;
- **495 CUC word nodes had multiple Burns annotations**;
- maximum annotations on one word: **7**;
- 862 nested/overlapping exact-span pairs were observed.

Restricting to positive statuses only:

- 1,456 CUC words carried at least one positive annotation candidate;
- **107** carried multiple positive annotations;
- maximum positive annotations on one word: **4**;
- 120 nested/overlapping positive annotation pairs were observed.

This directly validates the parent decision that scalar one-record-per-node features would be lossy. The authoritative module representation must preserve multiplicity, with convenience features treated only as derived projections.

## Comments/interpretive evidence

Among semantic annotations, 2,299 had non-empty comments; the aggregate probe detected 908 uncertainty signals and 329 cross-reference/alternative-reading signals. Therefore normalized source records must preserve comments and keep uncertainty/alternative interpretation distinct from homograph exclusion and α2/no-secure-cultic status.

## Consequences for child tickets

- #22 must model semantic status, worksheet role/provenance, uncertainty/comments, and stable source identity without collapsing multiplicity.
- #23 must use the real structural-shape evidence to bound its conservative reference grammar and must fingerprint 279 CUC tablet nodes.
- #26 must treat the probe's alignment results as lower-bound research evidence only and reproduce decisions with explicit production statuses/reasons.
- #27 must preserve multiple annotations on one CUC node losslessly.

Raw Burns source rows, references, headwords, comments, generated CSV, and generated TF output remain outside version control and must not be uploaded as review artifacts.
