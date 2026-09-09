# Research: Context-Fabric / cfabric-mcp consumer compatibility (#12)

## Question

Does the Text-Fabric artifact emitted by this repository satisfy the actual current Context-Fabric / `cfabric-mcp` corpus-loading boundary, and what smallest pinned downstream contract should CI preserve?

## Baseline

Repository baseline: `master@2808b7b8d7d62ad544c7e7238bb856a609dc3c6b`.

Current upstream evidence already proves:

- CSV and PDF paths build the same `TFData` graph through `build_tf_data()` and publish through the same `write_artifact()` path;
- real Text-Fabric 13.1 reload succeeds and section navigation works;
- CSV and PDF repeated-run semantic determinism is independently covered;
- the Agora manifest is validated against a pinned Agora revision.

What is missing is a real downstream Context-Fabric / MCP load of a generated artifact.

## Current downstream contract inspected

Pinned candidate consumer revision:

`alexsosn/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`

At that revision:

- `libs/core/pyproject.toml` identifies `context-fabric` version `0.5.7` and requires Python `>=3.13`;
- `libs/mcp/pyproject.toml` identifies `cfabric-mcp` version `0.1.7`, requires Python `>=3.13`, and depends on `context-fabric`;
- `cfabric_mcp.corpus_manager.CorpusManager.load(path, ...)` resolves the corpus directory, constructs `cfabric.Fabric(locations=str(path), silent="deep")`, and calls `loadAll(silent="deep")` when no feature subset is supplied;
- it then constructs `cfabric.results.CorpusInfo.from_api(...)`, which observes node-type levels, non-warp node/edge feature inventories, slot type/bounds and section types.

This makes `CorpusManager.load()` the highest-value single smoke boundary: it exercises the same Context-Fabric loader used by the MCP server and also forces the MCP-facing `CorpusInfo` discovery layer to understand the corpus. A separate direct `cfabric.Fabric` load would duplicate the inner operation without adding a distinct supported boundary.

## Runtime placement

Do not add Context-Fabric or `cfabric-mcp` to this project's runtime dependencies.

Reasons:

1. this converter supports Python >=3.10 while current Context-Fabric requires >=3.13;
2. materialization should remain usable by ordinary Text-Fabric users without installing an MCP server;
3. consumer compatibility is an integration contract, not a production implementation dependency.

Use a dedicated Python 3.13 CI job instead. Check out the exact pinned Context-Fabric commit and install its `libs/core` and `libs/mcp` packages only in that job.

The pinned Git revision identifies consumer source but not the complete transitive dependency closure. Therefore the dedicated job should also print the same canonical execution-environment/resolved-distribution evidence used by the ordinary test matrix after all project + consumer packages are installed and before the contract script runs.

## Fixture choice

One synthetic CSV materialization is sufficient for the consumer-format contract.

The consumer does not know whether a `WorkbookSource` originated in CSV or PDF; both adapters feed the same `build_tf_data()` graph/report/writer. Existing PDF real-parser evidence already proves that the PDF path reaches that common graph/writer and emits a semantically loadable Text-Fabric artifact. Running another real PDF parser inside the consumer job would therefore test extraction again rather than a new consumer boundary.

The consumer fixture should still be non-trivial:

- one worksheet path;
- one section;
- two records with distinct headwords/entries;
- Unicode transliteration;
- canonical KTU identifiers `1.14` and `1.16` so CUC normalization is observable;
- normal source provenance fields.

All data must be synthetic and generated in a temporary directory.

## Stable downstream observations

After materializing through the real CLI and loading through `CorpusManager`, assert only public/stable corpus semantics:

- `CorpusManager.list_corpora()` and `current` contain the explicitly supplied synthetic corpus name;
- returned `CorpusInfo.slot_type == "record"`;
- `max_slot == 2`;
- node-type inventory contains exactly the expected generated structure/counts: `record=2`, `worksheet=1`, `section=1`, `entry=2` (order should not be asserted unless required by the API);
- `section_types == ["worksheet", "section", "entry"]`;
- expected non-warp node features include at least `headword`, `ktu`, `cuc_tablet`, `language`, `source_file`, `source_row`, and `source_page`;
- loaded API record nodes expose headwords `bʿl`, `mlk`, KTU values `1.14`, `1.16`, CUC values `KTU 1.14`, `KTU 1.16`, and `language=Ugaritic`;
- the worksheet section reference resolves to `Synthetic/Worksheet`;
- Context-Fabric text rendering for each record returns the headword through the emitted `fmt:text-orig-full={headword}` format.

Do not assert cache directory layout, mmap filenames, compile timings, logging text, internal NumPy dtypes, or other Context-Fabric implementation details.

## Pinning strategy

The workflow should check out `alexsosn/context-fabric` at exact commit `3a38ca80e617d872ce1664e0f0740486d0e7e8ac` into a dedicated path such as `.context-fabric` and install:

- this repository (`.`);
- `.context-fabric/libs/core`;
- `.context-fabric/libs/mcp`.

The job itself should run on Python 3.13. It should not rely on a floating PyPI latest version for the consumer contract.

A future consumer update should intentionally change the pinned revision and rerun this contract, making incompatibility visible as a reviewed diff.

## TDD / evidence gate

No current production incompatibility has been demonstrated yet, so do not manufacture one in converter code.

Preserve a harness RED after research and plan:

1. add a dedicated `context-fabric-contract` job that installs the project and pinned consumer source;
2. add `scripts/check_context_fabric_contract.py` which creates the synthetic CSV input and materializes it through the real CLI;
3. after verifying required artifact files exist, deliberately raise `NotImplementedError("Context-Fabric consumer assertions not implemented")`;
4. exact-head CI must reach that seam after successful installation/materialization and fail there;
5. GREEN replaces only the seam with the real `CorpusManager` load/assertions unless that first real load exposes a genuine converter incompatibility.

If the real consumer load fails for output-format reasons, preserve that failing GREEN-attempt head as a genuine regression and research the smallest production correction before changing graph/writer semantics.

## Scope

This ticket establishes compatibility with one inspectable Context-Fabric/cfabric-mcp revision under one recorded execution environment. It does not claim compatibility with every future Context-Fabric release or make Context-Fabric a required runtime dependency of the converter.
