# Research: authoritative CUC compatibility fingerprint for Burns modules (#42)

## Current state

Burns already enforces a substantially stronger CUC compatibility contract than its durable metadata currently exposes.

`src/ugarit_context_parsing/cuc_index.py` hard-binds module construction to:

- repository `DT-UCPH/cuc`;
- commit `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- Text-Fabric version `0.2.8`;
- a deterministic required-file manifest SHA-256;
- exact size + SHA-256 for six files: `otype.tf`, `oslots.tf`, `tablet.tf`, `column.tf`, `line.tf`, `g_cons.tf`;
- exact node-type counts:
  - sign: 146017;
  - word: 27770;
  - line: 7616;
  - column: 334;
  - tablet: 279;
- exact `otext.tf` section schema:
  - section types: tablet, column, line;
  - section features: tablet, column, line.

After byte verification, `build_reviewed_cuc_index()` loads only the source features needed by Burns alignment/indexing (`tablet`, `column`, `line`, `g_cons`) plus Text-Fabric's warp/navigation machinery. It checks that structural sections, line→word descendants, tablet/column/line labels, and word `g_cons` inventory are internally coherent.

So the operational compatibility test already exists and is fail-closed. #42 should make that same contract inspectable and maintainable; it should not add a second validator or weaken the byte-level gate.

## Current durable metadata is incomplete

`src/ugarit_context_parsing/module.py` reduces the compatibility identity to:

```json
{
  "repository": "DT-UCPH/cuc",
  "commit": "ad69400f...",
  "version": "0.2.8",
  "manifest_sha256": "717e5b..."
}
```

That reduced payload is currently:

- embedded in every Burns `.tf` feature header as `cucRepository`, `cucCommit`, `cucVersion`, `cucManifestSha256`;
- embedded in `burns-module-report.json` under `cuc_compatibility`;
- checked again before writing the report/module.

What is missing from these durable artifacts is the structural compatibility contract that the code actually relies on: required source-feature inventory, expected node counts, and section schema. A maintainer inspecting a generated module cannot tell from its metadata which CUC structures/features were assumed without reading Burns source code.

## Single-source-of-truth requirement

Do not duplicate the fingerprint independently in module metadata, report code, and README.

The authoritative representation should be constructed in `cuc_index.py`, next to the constants and verifier that enforce it. `module.py` should consume a public immutable/canonical representation from there.

A suitable logical shape is:

```json
{
  "schema": "burns-cuc-compatibility-v1",
  "repository": "DT-UCPH/cuc",
  "commit": "...",
  "version": "0.2.8",
  "required_files_manifest_sha256": "...",
  "required_features": ["column", "g_cons", "line", "tablet"],
  "node_type_counts": {
    "column": 334,
    "line": 7616,
    "sign": 146017,
    "tablet": 279,
    "word": 27770
  },
  "section_types": ["tablet", "column", "line"],
  "section_features": ["tablet", "column", "line"]
}
```

The required-file per-file hashes/sizes remain authoritative validation data in code. Persisting all six per-file digests into every `.tf` feature header would be noisy and redundant because the already-persisted manifest SHA-256 commits to exactly that file fingerprint set. The report may expose the expanded per-file map if useful for maintenance diagnostics, but it is not necessary for a module consumer to establish identity.

## Feature metadata representation

Text-Fabric feature metadata are string-valued. Repeating a large nested JSON object in every feature header is undesirable.

Preserve the existing human-readable scalar fields (`cucRepository`, `cucCommit`, `cucVersion`, `cucManifestSha256`) for backwards compatibility. Add compact structural fields derived from the authoritative payload, for example:

- `cucCompatibilitySchema=burns-cuc-compatibility-v1`
- `cucRequiredFeatures=column,g_cons,line,tablet`
- `cucNodeTypeCounts=<canonical JSON>`
- `cucSectionTypes=tablet,column,line`
- `cucSectionFeatures=tablet,column,line`

All values must be deterministic strings produced from the same central fingerprint object. No path or local environment information belongs in TF metadata.

This makes a standalone feature file self-describing enough for compatibility review while preserving existing metadata consumers.

## Report representation

`burns-module-report.json` is the right place for the complete structured fingerprint because it already carries the authoritative materialization report.

Upgrade `cuc_compatibility` from the current four-field identity to the full versioned compatibility payload. Keep existing keys (`repository`, `commit`, `version`, `manifest_sha256` or a backwards-compatible alias) where practical so current consumers do not lose identity fields.

The report should include the structural values actually enforced at build time, not values recomputed from the generated Burns module. The reviewed CUC verifier remains authoritative.

A useful diagnostic extension is an expanded `required_files` object with each filename, byte size, and SHA-256. This is already immutable source data in `REVIEWED_CUC_FILES` and lets maintainers diagnose which upstream CUC file changed when reviewing a compatibility update. Because the report is one file, the verbosity cost is small.

## Documentation

README should gain one compact "CUC compatibility fingerprint" subsection that states:

- exact reviewed repository/commit/version;
- Burns relies on CUC `tablet`, `column`, `line`, and `g_cons` plus warp/navigation structure;
- exact reviewed node counts and section schema;
- generated TF feature headers carry the compact fingerprint and `burns-module-report.json` carries the expanded form;
- updating CUC requires deliberately reviewing/re-recording this fingerprint and rerunning the alignment/module integration evidence, not merely changing a version string.

The README should not duplicate six file hashes; direct maintainers to the report/source constants for those details.

## Update/maintenance semantics

A future CUC upgrade is not compatible merely because the same feature names exist. The current Burns alignment depends on stable node identities and structural navigation. Therefore the compatibility contract remains exact-reviewed-CUC, not a loose semantic-version range.

When reviewing a new CUC release/commit:

1. run the existing reviewed-CUC integration/audit against the candidate;
2. inspect changes in required files/features, warp counts, section schema and alignment outcomes;
3. update the authoritative fingerprint constants only as one reviewed change;
4. preserve RED evidence showing the old fingerprint rejects the candidate;
5. rerun module construction plus Context-Fabric composition and verify no silent node remapping;
6. only then publish the new compatibility fingerprint.

This ticket documents/exposes the existing exact compatibility boundary; it does not generalize Burns to multiple CUC versions.

## TDD requirements

Before production changes, preserve failing tests for:

- a public authoritative compatibility payload contains schema, exact identity, required features, node counts, section types/features, manifest digest, and expanded required-file fingerprints;
- its required feature set is exactly the set loaded by `build_reviewed_cuc_index()` (`tablet`, `column`, `line`, `g_cons`), with canonical deterministic ordering;
- module feature metadata retain the existing four scalar identity fields and add deterministic compact structural fields derived from the same payload;
- module report `cuc_compatibility` carries the complete structured fingerprint;
- changing a central fingerprint value changes both metadata/report projections rather than allowing them to drift independently;
- no local CUC path, platform, timestamp, or environment enters the fingerprint;
- existing exact-CUC byte/count/section rejection tests remain authoritative and green after implementation.

Use synthetic index/module fixtures for RED/GREEN; do not commit Burns-derived artifacts.

## Scope boundaries

#42 does not:

- relax the exact reviewed CUC requirement;
- add automatic CUC upgrades;
- change alignment semantics;
- change Burns feature payloads or node placement;
- change Agora parent resolution;
- redistribute CUC or Burns-derived data;
- change package/release version or licensing.
