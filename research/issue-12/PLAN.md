# Plan: pinned Context-Fabric / cfabric-mcp consumer gate (#12)

## Goal

Add a dedicated, pinned downstream compatibility gate proving that a real synthetic corpus emitted by `ugarit-context-parsing` loads through the current `cfabric-mcp` corpus manager and exposes the expected corpus structure/features/navigation.

## Preconditions

- Research: `research/issue-12/RESEARCH.md`.
- Baseline: `master@2808b7b8d7d62ad544c7e7238bb856a609dc3c6b`.
- Pinned consumer revision: `alexsosn/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`.
- The consumer job runs only on Python 3.13; no Context-Fabric dependency is added to `pyproject.toml`.
- Existing CSV/PDF Text-Fabric determinism and Agora gates remain unchanged.

## RED slice

### Dedicated workflow job

Extend `.github/workflows/test.yml` with `context-fabric-contract`.

The job must:

1. check out this repository;
2. check out `alexsosn/context-fabric` at exact revision `3a38ca80e617d872ce1664e0f0740486d0e7e8ac` into `.context-fabric`;
3. set up Python 3.13;
4. install this repository plus `.context-fabric/libs/core` and `.context-fabric/libs/mcp`;
5. record the canonical Python/platform/full resolved-distribution environment and SHA-256 after installation;
6. run `python scripts/check_context_fabric_contract.py`.

Do not upload generated corpus/cache artifacts.

### RED contract script

Add `scripts/check_context_fabric_contract.py` before any downstream assertions.

It must:

1. create an ephemeral synthetic CSV tree at `Synthetic/Worksheet.csv` using the production `WORKBOOK_FIELDS`;
2. write two records with distinct headwords (`bʿl`, `mlk`), KTU values (`1.14`, `1.16`), source pages, and original synthetic provenance text;
3. invoke the real `ugarit_context_parsing.cli.main()` with `convert ... --input-format csv` into a fresh temporary output directory;
4. require return code `0` and the four required artifact paths (`otype.tf`, `oslots.tf`, `otext.tf`, `conversion-report.json`);
5. then raise exactly `NotImplementedError("Context-Fabric consumer assertions not implemented")`.

At the RED head, no production converter code changes. Exact-head CI must show the new consumer job successfully checks out/installs the pinned consumer and materializes the corpus, then fails only at the deliberate seam.

The ordinary Python matrix and Agora job should remain green on that same head.

## GREEN slice

Replace only the deliberate seam unless a genuine consumer incompatibility is exposed.

Import `CorpusManager` from `cfabric_mcp.corpus_manager` and:

1. instantiate a fresh manager;
2. call `manager.load(str(output), name="burns-synthetic")` with no feature subset so the real path executes `cfabric.Fabric(...).loadAll()`;
3. obtain the loaded API via `manager.get_api()`;
4. assert stable consumer semantics.

### Corpus manager/discovery assertions

- `manager.list_corpora() == ["burns-synthetic"]`;
- `manager.current == "burns-synthetic"`;
- returned `CorpusInfo.slot_type == "record"`;
- `max_slot == 2`;
- section types equal `worksheet, section, entry`;
- node type counts, compared as a type→count mapping, equal:
  - record: 2
  - worksheet: 1
  - section: 1
  - entry: 2
- non-warp node feature inventory contains at least:
  - `headword`
  - `ktu`
  - `cuc_tablet`
  - `language`
  - `source_file`
  - `source_row`
  - `source_page`

Do not assert the ordering of node types or feature names.

### Loaded API assertions

- record nodes are `(1, 2)` after integer normalization;
- `headword`: `bʿl`, `mlk`;
- `ktu`: `1.14`, `1.16`;
- `cuc_tablet`: `KTU 1.14`, `KTU 1.16`;
- `language`: `Ugaritic`, `Ugaritic`;
- `source_file`: `Synthetic/Worksheet.csv` for both records;
- `source_row`: `1`, `2`;
- worksheet navigation resolves to `Synthetic/Worksheet`;
- `api.T.text(record)` returns the corresponding headword, proving the emitted text format works in Context-Fabric.

If `CorpusManager.load()` or these stable semantics fail because Context-Fabric interprets valid emitted TF differently from classic Text-Fabric, stop and preserve that failing head. Research the actual format delta before any production change.

## Exact-head GREEN gates

Require:

- existing Python 3.10 / 3.12 / 3.13 full test jobs green;
- existing environment-recording and installed-package checks green in those jobs;
- existing pinned Agora contract green;
- new `context-fabric-contract` green on Python 3.13;
- consumer job environment evidence emitted after all pinned consumer/project packages are installed;
- no generated Burns/TF/Context-Fabric cache artifact committed or uploaded.

## Independent adversarial review

Freeze the final head and independently challenge:

1. Is the consumer revision exact, or can CI drift to a different Context-Fabric source revision?
2. Does the job install both core and MCP from that same checkout?
3. Does the script invoke the real converter/writer rather than constructing `.tf` files itself?
4. Does `CorpusManager.load()` run with no feature subset, thereby exercising its normal `loadAll()` path?
5. Could the assertions pass without Context-Fabric actually loading the generated artifact?
6. Are CUC identifiers generated by production code rather than supplied by the fixture?
7. Are assertions limited to stable corpus semantics rather than mmap/cache internals?
8. Does the job accidentally add Context-Fabric to runtime dependencies or reduce Python 3.10/3.12 support?
9. Does environment evidence capture the resolved consumer dependency closure?
10. Is one CSV fixture justified by the already-reviewed common graph/writer boundary, without overstating direct PDF consumer replay coverage?
11. Are all inputs original synthetic data and all generated artifacts ephemeral?

Any blocker starts a regression/research sub-loop and requires fresh exact-head CI and review.

## Definition of done

- research → plan → deliberate consumer-harness RED → GREEN history is preserved;
- pinned Context-Fabric/cfabric-mcp source is installed in a dedicated supported-runtime job;
- real emitted corpus loads through `cfabric_mcp.corpus_manager.CorpusManager` and exposes expected MCP-facing structure/features/navigation/text;
- all existing repository gates remain green;
- independent adversarial review finds no blocker before merge.
