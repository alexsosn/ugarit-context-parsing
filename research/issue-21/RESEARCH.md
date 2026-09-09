# Research: Burns as a CUC-aligned Text-Fabric module (#21)

## Question

What is the correct product/data model for preserving Burns' cultic-vocabulary annotations against the Copenhagen Ugaritic Corpus (CUC), without duplicating CUC's diplomatic text or creating a second incompatible Text-Fabric warp?

## Baseline

Repository baseline: `master@ed498879dfdbf3399af7b904f300db5e0c41d657`.

The current materializer treats each Burns Workbook row as a Text-Fabric `record` slot and builds its own `worksheet → section → entry` warp. That model was useful for proving lossless parsing, deterministic TF writing, Agora execution, and Context-Fabric loading, but it duplicates corpus structure instead of enriching the Ugaritic text that Burns actually cites.

The target architecture is a feature-only Text-Fabric module constructed around a reviewed CUC warp.

## Burns source semantics

### Parser contract already present in this repository

The real PDF parser documents the nine source columns:

- A: headword / classified cultic term;
- B: KTU text number;
- C: references / attestations within the text;
- D: locus;
- E: room;
- F: point;
- G: depth;
- H: disputed findspot flag;
- I: comments.

The parser additionally preserves:

- source PDF page;
- worksheet-relative source file;
- source row after normalization;
- Burns section banner;
- Cultic Actions root/group label where present;
- repaired Unicode transliteration;
- explicit editorial headword corrections already documented in parser code.

Merged source cells are intentionally forward-filled: one headword can span several KTU rows, and one KTU/reference cell can span several findspot subrows. Wrapped references/comments/headwords are reassembled before records are materialized. This means a `WorkbookRecord` is a normalized scholarly source record, not necessarily a one-to-one textual occurrence.

`Not attested...` rows are explicitly non-textual notes. The parser folds their visually spilled cells back into `references` and clears findspot columns. They must remain represented in an alignment report but cannot be attached to a CUC text node merely to force coverage.

### Thesis description of Column C

Burns' Chapter 5 describes Column B as the KTU text identification number and Column C as the location of the identified lexeme within the text. Most Column C values are line references. Arabic numerals identify line numbers; uppercase Roman numerals identify columns when required.

The source therefore gives a principled grammar hierarchy:

`KTU tablet` + optional `Roman column` + one or more `Arabic line references`.

The parser preserves the source reference text as a string rather than interpreting it. Parsing that string belongs in the new alignment layer.

### Real-source audit limitation in this session

The repository pins the official Workbooks archive:

- White Rose eTheses URL: `https://etheses.whiterose.ac.uk/id/eprint/15038/4/Workbooks.zip`
- SHA-256: `4f90bf6f01d59a0fd71da9af57c8e64adc886aa32f8bf81b7d4426316b3e5d29`
- expected size: 4,868,771 bytes.

The connected web transport exposes the thesis PDFs/landing page but does not return the ZIP payload, and this execution container has no general network path to download it. Therefore this research does **not** claim a measured frequency distribution of every raw reference form or a complete Burns→CUC coverage percentage yet.

The implementation must support an explicit user-local audit command which reads the pinned/locally supplied Workbooks and produces the complete alignment-disposition report. Normal CI should use synthetic fixtures for grammar/alignment invariants and must not commit or upload Burns-derived rows/module output.

## CUC 0.2.8 contract

Reviewed CUC repository revision:

`DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`

At this revision, `tf/0.2.8` is the current reviewed CUC TF dataset.

### Warp and hierarchy

`otype.tf` establishes the exact node layout:

- `1–146017`: `sign` slots;
- `146018–146351`: `column`;
- `146352–153967`: `line`;
- `153968–154246`: `tablet`;
- `154247–182016`: `word`.

`otext.tf` defines sections as:

`tablet,column,line`

The key CUC lookup features are:

- `tablet` (`str`), e.g. `KTU 1.14`;
- `column` (`str`), uppercase Roman values such as `I`, `II`, `III`;
- `line` (`int`);
- `g_cons` (`str`) on words, consonantal transliteration.

CUC's reviewed/auto-parsing source also uses human-readable locations such as `KTU 1.14 II:3`, which matches the tablet/column/line hierarchy required for Burns alignment.

### Exact compatibility fingerprint

A module that stores values by CUC node ID must not treat `version=0.2.8` alone as sufficient compatibility evidence. Node IDs changed across earlier CUC versions, and a future regenerated 0.2.8-shaped tree could in principle retain a semantic version while changing node identity.

The v1 module should bind to all of:

- repository: `DT-UCPH/cuc`;
- reviewed Git commit: `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- CUC TF version: `0.2.8`;
- `otype.tf` blob SHA: `da808327be7f5cb2b1bd9dcf6f310dc5a4fd9e2e`;
- `oslots.tf` blob SHA: `2dfbec35f8e108d210bb885e5b8bc37ddf9b5bf8`;
- `otext.tf` blob SHA: `ddeb8a53174339d0ac008485cc6203362c5dd819`;
- expected node type/range summary above.

For lookup semantics, recording the reviewed feature identities is also useful:

- `tablet.tf`: `8e79f4f2d3ccb3751af681f7bca0d29fc5159446`;
- `column.tf`: `543dd6552d7d63713d2982ae9eb92a3878d0be58`;
- `line.tf`: `1c87333c3b5e7bd6d863ee01b0564f8566a00b13`;
- `g_cons.tf`: `804ffd90c7002b54552fb3e949e70951678d18ce`.

The writer/load contract should fail closed when the supplied base corpus does not match the reviewed warp fingerprint.

### CUC coverage boundary

CUC currently contains 278 tablets and its README publishes the included KTU ranges. Burns' Workbooks were constructed from a broader KTU corpus, so some Burns tablet identifiers can legitimately be absent from CUC 0.2.8.

Those records are `out_of_cuc`, not parser/alignment errors. They remain in the alignment report and receive no TF feature value until the base corpus contains an eligible anchor.

A complete user-local run must quantify dispositions from the actual Workbooks; this research cannot responsibly invent that percentage without the restricted source payload.

## Text-Fabric module architecture

Text-Fabric's data model explicitly distinguishes the warp (`otype`, `oslots`) from feature wefts. A dataset containing only wefts around another dataset's warp is a module.

The current Text-Fabric API supports loading multiple modules/locations and saving arbitrary node/edge features separately. `Fabric.save(nodeFeatures=..., edgeFeatures=..., metaData=..., location=..., module=...)` writes the supplied feature data; it does not require that every save operation own a warp.

Text-Fabric's sharing documentation uses `use(..., mod=...)` to load independently distributed data modules against a base corpus.

### BHSA-family reference modules

The inspected ETCBC modules provide four useful patterns:

1. `ETCBC/phono` ships `otext@phono.tf` plus node features (`phono.tf`, `phono_trailer.tf`) and no private `otype.tf`/`oslots.tf`. Its metadata declares `coreData=BHSA` and versions/provenance.
2. `ETCBC/valence` ships multiple node features keyed to existing BHSA node IDs, again with `coreData=BHSA`/`coreVersion` metadata.
3. `ETCBC/parallels` ships valued edge features such as `crossref`, `crossrefLCS`, and `crossrefSET`; it demonstrates richer relations between **existing** base nodes without adding a warp.
4. `ETCBC/bridging` ships feature-only data tied to `coreData=BHSA`; the inspected 2021 module directory contains `osm.tf` and `osm_sf.tf` only.

The common rule is the one needed here: modules enrich an existing node universe; they do not create an unrelated private textual hierarchy.

## Alignment model

### Stable source annotation identity

Every normalized Burns source record needs a stable ID independent of CUC node IDs. V1 should derive it deterministically from source identity, not sequence state in a generated graph.

Recommended input tuple:

- normalized relative worksheet/source file;
- source row;
- normalized scholarly fields that define the record (`section`, `root`, `headword`, `ktu`, `references`, findspot fields, comments).

A human-readable prefix plus truncated/full SHA-256 can provide stable IDs while preserving collision detection in the report. The exact canonical serialization belongs in the first implementation slice and must be tested for path/root independence and input-order independence.

### Reference parsing

The reference parser should produce structured targets rather than immediately selecting CUC nodes.

Minimum target representation:

- canonical tablet ID (`KTU n.nnn`);
- optional uppercase Roman column;
- line selector(s), preserving single lines, lists, and explicit ranges when grammar proves them;
- original reference string;
- parse status/reason.

Rules should be conservative. Unsupported punctuation, uncertain references, cross-references (`cf.`), prose, damaged/ambiguous syntax, or a reference that can be interpreted more than one way must not be silently normalized.

### CUC index

Build a deterministic index from a loaded, fingerprint-verified CUC API:

- tablet label → tablet node;
- `(tablet, column)` → column node(s);
- `(tablet, column, line)` → line node(s);
- line node → contained word nodes;
- word node → `g_cons`.

Uniqueness is an assertion. Duplicate structural keys in the reviewed base corpus are an explicit compatibility/index failure, not a reason to pick one arbitrarily.

### Smallest defensible anchor

For each normalized Burns record:

1. `non_textual`: `Not attested`/source note — no node.
2. `out_of_cuc`: canonical KTU tablet absent — no node.
3. `unresolved_reference`: source reference cannot be parsed/resolved — no node.
4. tablet-level annotation: if Burns identifies a text/context but no textual location, anchor the tablet node.
5. line-level annotation: if a parsed reference uniquely identifies line(s), anchor the line node(s).
6. word-level annotation: only if the Burns headword/lexeme can be matched unambiguously among `g_cons` words inside the resolved line target.
7. `ambiguous`: multiple plausible lines/words or conflicting evidence — no guessed narrower target.

A record that cites multiple lines may legitimately produce multiple anchored occurrences under one stable Burns annotation ID. The report must distinguish one source annotation from its zero/one/many CUC anchor nodes.

## Multiplicity without annotation nodes

TF node features are single-valued per node. Multiple Burns source annotations can map to the same CUC word/line/tablet, so a naive feature-per-field mapping would overwrite data.

Creating Burns annotation nodes is excluded because that would modify/extend the node universe and require its own `otype`/`oslots` semantics.

Valued edge features cannot solve the primary record-storage problem either: TF edges can only connect existing node IDs, while a Burns annotation ID is not a CUC node.

### Recommended v1 representation

Use two layers:

1. **Canonical lossless node payload** on each anchored CUC node: a deterministic compact JSON array of annotation/occurrence objects, stored as a string node feature such as `burns_annotations`. Objects contain stable Burns annotation ID and the normalized metadata needed for that anchor. Ordering is canonical by annotation ID/occurrence target.
2. **Derived query-friendly node features** containing deterministic set/projection values, e.g. `burns_present`, `burns_headwords`, `burns_roots`, `burns_sections`, `burns_workbooks`, and possibly disposition/anchor-kind summaries. These are derived conveniences; the JSON payload/report is authoritative for multiplicity.

All source records, including records with no CUC anchor, are also written to `alignment-report.json`. That report is the complete accounting surface and includes source counts, disposition counts, compatibility fingerprint, stable annotation IDs, parsed targets, selected CUC nodes, and explicit reasons.

Text-Fabric's writer handles string feature escaping, so the implementation should pass canonical JSON strings through `Fabric.save()` rather than manually inventing TF escaping. Tests must reload the generated module and compare decoded payloads, including a node with multiple annotations and comments containing punctuation/newlines.

## Module output contract

A Burns CUC module output directory may contain:

- `burns_annotations.tf` — canonical node payload;
- query convenience node features;
- optional `otext@burns.tf` only if module-specific display formats become useful;
- `alignment-report.json` (non-TF sidecar evidence).

It must **never** contain:

- `otype.tf`;
- `oslots.tf`;
- a copy of CUC text/sign/word/line/tablet features;
- Burns-derived PDF/CSV source files.

Module feature metadata should declare at least:

- `coreData=CUC`;
- `coreVersion=0.2.8`;
- exact CUC repository/commit/warp fingerprint;
- Burns source/provenance description;
- generator/version identity;
- Burns source-data licensing boundary.

## Loading and consumer contracts

### Text-Fabric

The integration gate should use a pinned/local CUC 0.2.8 checkout and load base + Burns module as separate modules/locations. It must prove:

- CUC slot type remains `sign`;
- max slot/max node and every base `otype` count are unchanged;
- base `otype`/`oslots` semantics are unchanged;
- Burns features appear on the expected existing node IDs;
- a multiply annotated node round-trips all source annotation IDs.

### Context-Fabric / cfabric-mcp

The current repository already pins a real Context-Fabric/cfabric-mcp consumer revision. The combined contract should load the CUC base plus Burns module through the supported consumer module-loading path if available. If the current MCP corpus manager only accepts one directory and does not expose TF module composition, stop at a preserved failing consumer seam and research/extend the consumer contract separately rather than copying CUC files into the Burns output directory.

## Product migration

The existing standalone row-slot materializers must not disappear before the replacement module reaches combined Text-Fabric and Context-Fabric compatibility. During migration they should be clearly marked provisional/deprecated.

Agora registration/composition comes last. Agora should eventually express:

CUC base corpus + Burns user-local source → Burns feature module → CUC+Burns consumer

rather than registering Burns as an independent textual corpus.

## Implementation slicing

#21 is too broad for a single safe production PR. The work should be split into independently reviewable tickets after this parent research/plan:

1. normalized Burns annotations + stable IDs;
2. conservative KTU/reference grammar + pinned CUC index/fingerprint;
3. alignment engine + complete disposition report;
4. feature-only TF module writer + multiplicity round-trip + combined TF load;
5. combined Context-Fabric contract + standalone materializer deprecation;
6. downstream Agora composition/registration after upstream model is proven.

Every child ticket must preserve its own research → plan → RED → GREEN → CI → independent-review history.

## Research conclusions

- Burns' scholarly object is an annotation/occurrence tied to KTU text locations, not an independent text slot.
- CUC 0.2.8 supplies the authoritative text/node universe and must be pinned by exact warp identity.
- Conservative parsing and explicit unresolved/out-of-CUC dispositions are required because source references are editorial strings and CUC is incomplete relative to KTU.
- No annotation nodes are required for v1; canonical structured node payloads + convenience features + a complete alignment report preserve multiplicity without changing CUC's warp.
- Feature-only TF modules are a well-established Text-Fabric pattern and match the BHSA reference architecture.
- Real-source coverage quantification must be performed user-locally from the pinned Workbooks archive; it cannot be fabricated from incomplete source access in this research session.
