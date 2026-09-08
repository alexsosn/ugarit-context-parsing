# Issue #1 implementation plan

This plan follows the research decision in `RESEARCH.md`. Production behavior is not added until the RED test commit exists.

## Slice 1 — package and converter contracts (RED)

Add synthetic tests that import the future package and define the public contracts before implementation:

1. `normalize_cuc_tablet()`
   - `1.14` → `KTU 1.14`
   - `KTU 1.14` → `KTU 1.14`
   - whitespace is normalized
   - `Not attested` and non-KTU prose → empty join key
2. CSV loader
   - recursively discovers files in deterministic path order;
   - exact Workbook header contract;
   - every input row and every Workbook field survives;
   - records use relative source paths and 1-based source row numbers;
   - malformed/missing headers fail closed.
3. Graph builder
   - one `record` slot per row;
   - slot ids are first and contiguous;
   - non-slot types occupy contiguous blocks;
   - every non-slot node has non-empty `oslots`;
   - worksheet/section/entry spans match the synthetic source;
   - all Workbook fields are preserved;
   - `language=Ugaritic` and `cuc_tablet` are additive features, not replacements.
4. Conversion report
   - no source row bodies or absolute local paths;
   - deterministic counts/source hash/checks;
   - graph invalidity produces `status != ok`.
5. Manifest contract
   - two materializer ids;
   - user-local directory acquisition only;
   - CSV and PDF globs are separate;
   - direct Python-module execution;
   - network denied;
   - required TF/report output paths.

RED evidence: commit tests before creating the package/module/manifest. A test run must fail only because the intended production symbols/files are absent.

## Slice 2 — core CSV → TF graph (GREEN)

Implement:

- `src/ugarit_context_parsing/model.py`: immutable record/source models;
- `src/ugarit_context_parsing/csv_source.py`: schema validation/discovery/loading;
- `src/ugarit_context_parsing/graph.py`: TF payload, builder, validation, metadata;
- `src/ugarit_context_parsing/report.py`: semantic report;
- `src/ugarit_context_parsing/writer.py`: staged `Fabric.save` serialization/publication;
- `src/ugarit_context_parsing/cli.py`: `convert SOURCE --input-format csv --output OUTPUT`;
- `src/ugarit_context_parsing/__init__.py`: version.

Package requirements:

- Python >=3.10;
- `text-fabric>=13.1,<14`;
- normal build backend and console script;
- development test dependency.

Test gates:

- unit tests for all RED contracts;
- CLI conversion on synthetic CSV source;
- load the generated output with Text-Fabric and assert slot/node/features/section navigation.

## Slice 3 — PDF adapter through the existing parser

Avoid a second independent PDF interpretation.

Refactor `scripts/parse_workbooks_to_csv.py` so the source-sensitive parsing implementation is importable from the installed package while preserving the historical script CLI behavior. The package must expose a `parse_workbook_pdf(path)` function used by both:

- the legacy CSV-generation script;
- `ugarit_context_parsing.cli --input-format pdf`.

The standalone script keeps source download/orchestration in `scripts/sources.py`; the installed materializer path consumes only the provided local directory and never calls `ensure()`/downloads.

TDD gate for this slice:

- add a regression that supplies a synthetic/monkeypatched parser result and proves PDF and CSV feed the same graph path;
- add an import/packaging regression proving the PDF parser exists after project installation/import;
- if a small synthetic PDF fixture can be generated in CI without embedding copyrighted source material, add a real parser smoke; otherwise rely on the existing parser's source-specific tests/manual evidence and test the materializer adapter independently.

## Slice 4 — Agora manifest and project metadata

Add `agora.materializer.json`:

- plugin id `ugarit-context-parsing`;
- version matching `pyproject.toml`;
- repository `alexsosn/ugarit-context-parsing`;
- materializers:
  - `burns-workbooks-csv-text-fabric`
  - `burns-workbooks-pdf-text-fabric`.

Both require:

- `user-local` directory acquisition;
- `allow_symlinks: false`;
- `python-module` execution via `ugarit_context_parsing.cli`;
- `network: deny`;
- `otype.tf`, `oslots.tf`, `otext.tf`, `conversion-report.json`.

Validate against the current Agora materializer-plugin JSON schema. Keep a vendored test fixture/simplified structural assertion only if networkless local tests cannot read Agora; CI may fetch/checkout Agora for the authoritative contract smoke.

## Slice 5 — CI and documentation

Add a repository workflow on supported Python versions (minimum 3.10 plus Agora-relevant 3.12/3.13) that runs:

- unit tests;
- synthetic CSV CLI E2E;
- Text-Fabric load smoke;
- package build/install/import smoke;
- manifest schema validation.

README additions:

- local `csv → TF` and `pdf → TF` usage;
- graph schema and CUC join semantics;
- explicit statement that generated TF remains Burns-derived/local under the source licence;
- Agora manifest/materializer ids;
- clarify Appendix is not part of the first materializer.

## Slice 6 — exact-head test gate

Before final review:

- all repository tests green;
- generated synthetic TF loads with Text-Fabric 13.x;
- manifest validates against Agora current schema;
- package installs on an Agora-supported Python runtime;
- inspect final diff for accidental real source/derived data;
- verify no network access in converter execution path;
- verify no absolute user paths in TF/report.

## Slice 7 — logically independent adversarial review

Perform a fresh review from the PR patch rather than from implementation notes. Review dimensions:

1. **Scholarly semantics** — any CUC feature/node name asserting more than Burns encodes?
2. **Losslessness** — can any CSV field/row disappear, merge, or be normalized destructively?
3. **TF invariants** — contiguous slots/type blocks, valid oslots, loadable section hierarchy, feature metadata.
4. **Security** — symlinks, traversal, output replacement, manifest shell/network escape.
5. **Licensing/privacy** — no real derived fixture, no CUC licence copied onto Burns data, no absolute source paths.
6. **Reproducibility** — deterministic discovery/order/hash/report and no wall-clock-dependent semantic output.
7. **Packaging** — installed module includes everything needed for PDF mode; no dependence on repo-only `scripts/` paths.
8. **Agora boundary** — manifest matches v1 contract and does not claim automatic composition that Agora has not implemented.

A blocking finding requires:

- a focused regression test observed RED;
- minimal production fix;
- full GREEN test gate;
- fresh adversarial review of the new exact head.

## Slice 8 — Agora registration (separate PR/repo)

Only after this upstream PR is green and reviewed:

1. pin the immutable upstream commit in `Agora/registry/materializers.yaml`;
2. add a RED registry test for repository/ref/version/manifest/materializer ids;
3. add/extend live installer smoke to passive-fetch, explicit-install, inspect receipt/dependencies/manifest, and import `ugarit_context_parsing.cli`;
4. where feasible, run synthetic local materialization under Agora's real sandbox and load the artifact with Context-Fabric/Text-Fabric;
5. document that automatic resource→materializer→consumer composition remains a separate Agora concern;
6. run Agora Foundation/materializer workflows;
7. perform a second logically independent adversarial review of the Agora PR.

## Completion condition

Issue #1 is complete when the upstream converter PR is merged after exact-head GREEN + independent review. The user's end-to-end goal is complete when the separate Agora registration/install PR is also merged after its own RED→GREEN→review loop.
