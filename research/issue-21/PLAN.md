# Plan: replace standalone Burns TF corpus with a CUC annotation module (#21)

## Preconditions

- Parent research: `research/issue-21/RESEARCH.md`.
- Baseline: `master@ed498879dfdbf3399af7b904f300db5e0c41d657`.
- Reviewed base corpus: `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`, TF version `0.2.8`.
- No Burns-derived PDF, CSV, TF module, or alignment payload may be committed/uploaded.
- Existing standalone materializers remain available until replacement combined-load/consumer gates pass.

## Architecture

The final data flow is:

`Burns PDF/CSV → normalized Burns annotations → conservative KTU/reference targets → fingerprinted CUC index → alignment dispositions/anchors → feature-only Burns TF module + alignment report → CUC+Burns Text-Fabric → Context-Fabric/cfabric-mcp`

CUC owns `otype`/`oslots` and all diplomatic text nodes. Burns owns feature wefts and sidecar provenance/alignment evidence only.

## Workstream 1: normalized annotation model and stable IDs

### Research/contract

Define an immutable `BurnsAnnotation` model derived from `WorkbookRecord` which preserves:

- source file/row/page;
- workbook/worksheet identity derivable from relative source path;
- section;
- root;
- headword;
- raw KTU;
- raw references;
- locus/room/point/depth/disputed;
- comments;
- explicit textual/non-textual source classification.

Define deterministic canonical serialization and stable annotation IDs independent of absolute source root and input filesystem creation order.

### RED

Add tests before implementation requiring:

- exact source-field preservation;
- stable ID equality for the same relative source record under different absolute roots/order;
- stable ID change when a scholarly record field changes;
- explicit `non_textual` classification for `Not attested` records;
- no CUC node IDs in this model.

### GREEN

Implement only the normalization/identity layer and use it from both CSV and PDF source adapters. Do not alter current graph/writer output yet.

## Workstream 2: KTU/reference grammar and CUC compatibility/index

### Reference grammar RED/GREEN

Introduce a structured target type and conservative parser. Synthetic fixtures must cover at least:

- tablet-only KTU;
- Arabic line number without column;
- uppercase Roman column + line;
- multiple line numbers;
- explicit line range where the source syntax is established;
- wrapped whitespace;
- `Not attested`;
- prose/cross-reference/uncertain unsupported strings;
- ambiguous syntax that must remain unresolved.

The parser must retain original text and reason codes. It may not guess punctuation semantics unsupported by Burns' documented convention.

### CUC fingerprint/index RED/GREEN

Add a pinned CUC 0.2.8 integration fixture/job. Require exact reviewed fingerprint:

- repo/commit/version;
- warp feature identities;
- expected type/range counts.

Build deterministic indexes for tablet, column, line and contained words/`g_cons`. Duplicate structural keys fail closed.

Do not vendor CUC TF data into this repository; CI may check out the exact public CUC revision in a dedicated job.

## Workstream 3: alignment engine and accounting report

### RED

Synthetic CUC/API fixtures must prove dispositions:

- `non_textual`;
- `out_of_cuc`;
- `unresolved_reference`;
- unique tablet anchor;
- unique line anchor;
- unique word anchor from line + headword/g_cons;
- ambiguous word hit;
- multi-line/multi-anchor record;
- conflicting or duplicate structural target failure.

### GREEN

Implement pure alignment logic returning immutable result objects. Never let lookup code choose the first of multiple hits.

Generate deterministic `alignment-report.json` which accounts for **every** input annotation ID exactly once at the source-record level and records zero/one/many anchor occurrences.

A user-local audit command must load actual Workbooks, verify/record source tree identity, run against the pinned CUC base, and report disposition counts/coverage without uploading data.

## Workstream 4: feature-only Text-Fabric module writer

### Representation

Authoritative aligned-node feature:

- `burns_annotations`: deterministic compact JSON array string, containing stable annotation/occurrence records.

Query convenience features should be additive projections, initially limited to demonstrated needs such as:

- `burns_present`;
- `burns_headwords`;
- `burns_roots`;
- `burns_sections`;
- `burns_workbooks`;
- `burns_anchor_kinds`.

Avoid proliferating convenience features until tests/search use cases justify them.

### RED

Before writer implementation require:

- generated module contains no `otype.tf`;
- generated module contains no `oslots.tf`;
- no CUC diplomatic feature copy;
- one base node with two annotations round-trips both losslessly;
- canonical ordering makes repeated writes deterministic;
- punctuation/newlines/Unicode comments survive Text-Fabric escaping/reload;
- compatibility metadata contains reviewed CUC fingerprint;
- failed write cannot publish a partial/stale module/report set.

### GREEN

Use Text-Fabric's feature writer (`Fabric.save`) for feature encoding rather than hand-escaping TF syntax. Publish module feature set + alignment report transactionally.

## Workstream 5: combined Text-Fabric integration

Add a pinned CUC 0.2.8 integration job which materializes a legal synthetic Burns module and loads CUC base + module separately.

Require:

- base slot type remains `sign`;
- max slot/max node and full base type counts are unchanged;
- original `otype`/`oslots` behavior is unchanged;
- Burns features are discoverable on expected CUC nodes;
- module payload multiplicity survives reload;
- base-only load still works;
- repeated module generation is semantically deterministic.

The module writer's definition of done is not satisfied by loading Burns output alone; it must load against the exact CUC warp.

## Workstream 6: Context-Fabric/cfabric-mcp integration

Research the pinned consumer's supported multi-location/module interface before implementation.

RED must exercise the real consumer boundary with CUC base and Burns module kept separate. If current `CorpusManager` cannot express module composition, preserve that failure and create/follow a consumer-side ticket; do not work around it by copying CUC into Burns output.

GREEN must prove feature inventory and at least one query/access path over Burns features while base CUC structure remains unchanged.

## Workstream 7: product migration and Agora

Only after Workstreams 1–6 pass:

1. mark current standalone Burns row-slot materializers deprecated/provisional in CLI/docs/manifest;
2. provide a migration command/path producing the CUC module from local Burns input;
3. decide whether to retain standalone mode temporarily as an explicitly legacy diagnostic export;
4. update Agora so Burns is represented as a materializer/module layered on the CUC resource rather than an independent corpus;
5. update release semantics/versioning after software license issue #15 is resolved.

Do not remove a working legacy path before the replacement is proven in both TF and Context-Fabric.

## Child-ticket strategy

Create separate implementation tickets for:

1. normalization/stable IDs;
2. reference grammar + CUC fingerprint/index;
3. alignment/report;
4. TF module writer + combined TF load;
5. Context-Fabric combined consumer + legacy deprecation;
6. Agora composition migration.

Each child ticket independently follows research → plan → RED → GREEN → current CI → logically independent adversarial review. Parent #21 remains open until the full replacement architecture is integrated.

## Cross-cutting gates for every child

- Existing Python 3.10/3.12/3.13 suite remains green unless a documented runtime boundary requires a dedicated newer job.
- CI provenance attestation remains green in every checkout job.
- Immutable GitHub Action pins remain unchanged unless separately researched.
- No source/network path weakens symlink validation or network-denied Agora execution semantics.
- No restricted Burns-derived artifact is committed/uploaded.
- No child may introduce new TF nodes/warp files under the guise of module metadata.
- Any real CUC consumer regression is preserved before corrective production changes.

## Parent completion criteria

#21 closes only when:

- the product path emits feature-only Burns data aligned to a fingerprinted CUC warp;
- every Burns source record has a deterministic ID and explicit alignment disposition;
- multiplicity is lossless;
- combined CUC+Burns loads in Text-Fabric and the intended Context-Fabric consumer;
- current standalone row-slot behavior is deprecated/replaced coherently;
- downstream Agora composition reflects the module relationship;
- complete user-local real-source audit is documented without redistributing Burns data;
- each implementation PR has current attested CI and independent adversarial review.
