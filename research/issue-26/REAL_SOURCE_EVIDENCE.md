# Real-source alignment evidence amendment (#26)

This amendment records the completed aggregate-only research workflow after the initial research and PLAN were committed. It does not widen the implementation scope or change the frozen alignment semantics; it replaces earlier lower-bound observations with attested counts from the checksum-pinned Workbooks and exact reviewed CUC base.

## Attested run

- PR head under test: `10bb938d858633d4dd5267d59d96a30abe7f002d`
- workflow run: `34364569062`
- job: `source-safe-alignment-audit` (`102509848634`)
- Burns Workbooks: checksum-pinned archive from White Rose, 45 PDFs
- reviewed CUC: `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`
- source tree SHA-256 observed in the transient run: `0488d3243661ed3553b56c53e29520a3687cc91a4ccf7c037c1cb527014306d9`

The workflow emitted aggregate counts only and uploaded no Burns-derived artifact.

## Source/accounting counts

- source records: **13,857**
- contiguous semantic annotations: **10,419**
- non-textual annotations: **748**
- parsed references: **9,491**
- invalid KTU: **85**
- malformed references: **37**
- unsupported references: **58**
- syntactically unresolved total: **180**
- out-of-CUC annotations: **4,343**
- tablet-only parsed annotations: **16**

Resolved line-shape evidence:

- unique bare-line targets: **5,329**
- unique explicit-column line targets: **4,120**
- ambiguous bare-line targets: **16**
- no matching CUC line: **51**
- annotations containing at least one unresolved/ambiguous line: **42**

The ambiguous bare-line cases had 2, 4, or 6 candidate CUC lines in this source run. This reinforces the #23/#26 rule that bare-line lookup may never choose the first candidate.

## Lexical normalization evidence

Burns headwords contain documented trailing editorial markers on **1,058** annotations. Comparing exact matching before and after stripping only the documented terminal marker set `*†!?` materially improves conservative matching:

- annotations with zero exact span matches, raw headword tokens: **3,445**
- annotations with zero exact span matches after documented marker stripping: **2,587**
- annotations with exactly one matched line after marker stripping: **1,732**
- lines with exactly one exact contiguous span after marker stripping: **4,316**
- lines with multiple exact contiguous spans after marker stripping: **169** (157 with two, 10 with three, 2 with four)

This supports the already-planned lexical rule: NFC + whitespace tokenization + stripping only the parser-documented trailing editorial markers + exact case-sensitive contiguous comparison to CUC `g_cons`. It does **not** justify fuzzy, morphological, punctuation-wide, root-substitution, or cross-line matching.

## Span/overlap lower bounds

The same source-safe run strengthens the earlier lower bounds:

- CUC words with multiple positive Burns annotations: **216**
- positive overlapping annotation pairs on the same resolved line: **222**
- maximum positive Burns annotations observed on one CUC word: **4**

These are empirical lower bounds for the reviewed source/base combination, not cardinality assertions for synthetic tests or future CUC versions. They confirm that one CUC word may legitimately participate in several independently identified Burns annotations and that nested/overlapping spans cannot be merged by node or headword.

## Process consequence

The temporary workflow served its research purpose and is removed after this evidence is recorded, avoiding permanent CI cost and avoiding perturbation of the repository's action-pin count contract. The reusable aggregate audit script remains under `research/issue-26/` as a user-local/source-safe research tool.

No production alignment code existed when this run completed. The RED commit remained tests-only.