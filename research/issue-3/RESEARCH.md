# Research: semantic determinism evidence for Burns CSV Text-Fabric materialization (#3)

## Question

Does the current Burns Workbook CSV materializer already produce deterministic scholarly/Text-Fabric content for an identical source tree under one fixed converter/dependency/runtime identity, and what exact comparison should serve as reproducible evidence for Agora cacheability review?

## Baseline inspected

- `master`: `e1218b88d9d849c58ee25541339f32b0d8f5a7d3`.
- package contract: `text-fabric>=13.1,<14`, Python >=3.10.
- relevant converter modules: `source.py`, `graph.py`, `report.py`, `writer.py`, and the existing real TF integration test.
- Text-Fabric writer implementation inspected at `annotation/text-fabric@1079c68e051947efd955b61ad499e3a9beb03b09` for serialization/header behavior.

This ticket is evidence work for the CSV path only. It does not claim PDF extraction determinism or cross-runtime/cross-Text-Fabric-version determinism.

## Source-order determinism

`load_csv_directory()` is deterministic for an unchanged source tree:

1. it considers only one-level `*/*.csv` Workbook files;
2. files are sorted by POSIX relative path before reading;
3. rows are consumed sequentially in CSV order;
4. each record carries deterministic relative `source_file`, ordinal `source_row`, and parsed source values;
5. `_tree_hash()` hashes those same sorted relative paths plus exact file bytes;
6. symlinks are rejected.

The source root's absolute pathname is not incorporated into the scholarly graph or source tree hash.

## Graph/node determinism

`build_tf_data()` allocates record slots by deterministic source-record order. Worksheet/section/entry groupings are accumulated in that same order, duplicate labels use deterministic occurrence counts, and non-slot nodes are allocated in the fixed type order `worksheet`, `section`, `entry`.

All generated node features derive only from source fields plus fixed converter constants/normalization. `oslots` sets are built from deterministic slot sequences.

Text-Fabric's `_writeDataTf()` sorts edge source nodes and converts edge target sets through normalized ranges; node features are likewise serialized by sorted node ID. Therefore Python set iteration does not become persisted scholarly ordering for this graph.

## Metadata determinism

Burns metadata in `graph.py` is fixed for a given converter commit. It contains no wall clock, host path, random identifier, process state, or environment-dependent value.

The conversion report is likewise deterministic for fixed source + graph:

- schema/converter identity are constants;
- source format/tree hash/file count derive from the fixed source;
- counts derive from the graph;
- checks are pure graph/source checks;
- no creation time or destination path is written.

The report should therefore be compared as a complete JSON object with **no exclusions**.

## Text-Fabric serialization volatility

Text-Fabric itself writes generated headers to feature/config files. Its current writer emits:

- `@writtenBy=Text-Fabric`;
- `@dateWritten=<current UTC time>`.

`dateWritten` is explicitly wall-clock-generated during save, so two correct fresh materializations need not have byte-identical `.tf` files. The `writtenBy` value is constant and does not need exclusion.

The smallest justified byte-level normalization is therefore:

- compare the exact set of generated `*.tf` filenames;
- for every file, compare all UTF-8 lines exactly **except lines beginning `@dateWritten=`**.

No other header/body field is currently justified as volatile. If a future Text-Fabric 13.x patch exposes another difference, the test must fail and force research rather than silently broaden exclusions.

This normalized-file comparison is stronger than sampling API features: it covers every persisted feature/edge/config datum and all metadata except the single proven generated timestamp.

## Independent reload/semantic check

The evidence must still load both fresh outputs independently with Text-Fabric, because normalized text equality alone does not prove that both artifacts form usable TF datasets.

After `Fabric(...).loadAll()` on each output, the test should compare at least:

- the complete loaded node-feature inventory (`Fall()`);
- the complete loaded edge-feature inventory (`Eall()`);
- the complete node-type sequence / maximum node and slot structure;
- Text-Fabric section/navigation behavior for every generated worksheet/section/entry node, not only one example.

Because normalized `.tf` files are already compared completely, these reload assertions are semantic/loader/navigation corroboration rather than a second partial serialization oracle.

## Synthetic fixture requirements

Use a legal synthetic CSV tree only. It should contain:

- at least two worksheet files so sorted file traversal is exercised;
- multiple records across sections/entries;
- Unicode Ugaritic transliteration, including `bʿl` or equivalent;
- normalized KTU identifiers;
- at least one repeated/empty-ish structural label case only if it remains readable and does not obscure the core evidence.

The fixture is generated inside a temporary directory; no Burns-derived content is committed.

## Input immutability / acquisition boundary

Record a cryptographic digest of every source file (or the source tree hash) before the first run and verify the same bytes after both runs. The CSV materializer receives only the supplied local directory and contains no acquisition/network step; the evidence test should call the real CLI/materializer directly and must not mock a network provider.

Agora separately binds plugin source, installed dependency tree, Python ABI/platform and runtime identity in `execution_identity_sha256`. This upstream test therefore proves determinism only **within one fixed execution identity**. It must not be cited as evidence that Text-Fabric 13.1 and a later 13.x patch, different Python/platforms, or changed dependencies necessarily emit identical content.

## TDD/evidence-gate decision

Current code inspection gives no identified scholarly nondeterminism defect. The only expected rerun byte difference is Text-Fabric's documented/generated `@dateWritten` header.

Therefore this ticket should **not manufacture a RED production defect**. Per issue #3's explicit evidence-test exception, the new repeated-run test may be GREEN on first execution. The gate is still research -> plan -> committed evidence test -> CI -> independent review. If the evidence test fails beyond `@dateWritten`, that failure becomes a genuine RED and production must remain unchanged until the new nondeterminism is researched.

## Downstream evidence target

The stable intended test target is:

`tests/test_text_fabric_integration.py::RealTextFabricIntegrationTests.test_repeated_synthetic_csv_materialization_is_semantically_identical`

After this exact commit is independently reviewed and merged, Agora may update its immutable Burns pin and use that target as exact-commit cacheability evidence for **`burns-workbooks-csv-text-fabric` only**.

PDF materialization remains unreviewed/non-reusable until separate legal synthetic-PDF repeated-run evidence exists.
