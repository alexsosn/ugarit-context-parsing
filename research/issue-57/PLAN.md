# Issue 57 plan: align conversion-report producer provenance

Research: `research/issue-57/RESEARCH.md`.

## Phase 1 — preserved RED

Add focused tests only; production remains unchanged.

Required contracts:

1. Build a normal synthetic legacy conversion report under the installed test environment and require:
   - `schema_version == 1` unchanged;
   - `converter.name == "ugarit-context-parsing"` unchanged;
   - `converter.version == importlib.metadata.version("ugarit-context-parsing")`.
   Current release metadata is 0.3.0, so the existing hard-coded 0.2.0 must fail.
2. Patch distribution metadata lookup to a synthetic future version (for example `9.8.7`) and require a newly built report to carry that exact producer version while `schema_version` stays 1. This proves report provenance follows the installed producer identity rather than another source-code constant.
3. Patch distribution lookup to raise `PackageNotFoundError` and require report construction to fail rather than emit a guessed/`unknown` producer version.
4. Keep the existing deterministic/counts/checks report assertions unchanged.

Expected RED: current `report.py` never consults installed distribution metadata and always emits `0.2.0`.

## Phase 2 — GREEN

In `src/ugarit_context_parsing/report.py`:

- import `importlib.metadata`;
- resolve `metadata.version("ugarit-context-parsing")` when constructing the `converter` object;
- do not catch `PackageNotFoundError` or invent a fallback;
- leave `schema_version`, report layout, counts and checks unchanged.

Do not modify package/manifest versions or introduce `__version__`/another version constant.

## Phase 3 — exact-head CI

Run the frozen head through:

- Python 3.10 / 3.12 / 3.13;
- installed-package smoke;
- Agora contract;
- Context-Fabric consumer contract;
- any reviewed-CUC/module workflows triggered by the touched tests/files.

## Phase 4 — logically independent adversarial review

Challenge independently:

- schema-version vs producer-version separation;
- whether distribution metadata really corresponds to the package under test;
- deterministic output within one installed release;
- behavior when package metadata is unavailable;
- whether old 0.2.0 reports remain acceptable to #54 ownership logic;
- accidental package/manifest/version changes;
- no coupling to module/CUC semantics.

Material findings require a separate review-derived RED before correction.

## Phase 5 — merge ordering

This is post-release maintenance. Keep the PR draft/unmerged until GitHub Release `v0.3.0` exists and resolves to frozen release commit `4994a45c53a73c09a4939731bc56af585b3ba30a`.
