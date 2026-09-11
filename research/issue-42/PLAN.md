# Plan: expose the authoritative CUC compatibility fingerprint (#42)

Research: `research/issue-42/RESEARCH.md`.

This ticket exposes the exact CUC contract Burns already enforces. It does not relax compatibility, change alignment/node placement, add parent acquisition, or change release/license metadata.

## Slice 1 — canonical public fingerprint

### RED

Add focused tests requiring `ugarit_context_parsing.cuc_index.reviewed_cuc_compatibility_payload()` to return one deterministic payload with:

- schema `burns-cuc-compatibility-v1`;
- exact reviewed repository, commit, TF version, and required-files manifest SHA-256;
- exact required source features, canonically ordered as `column,g_cons,line,tablet`;
- exact reviewed node-type counts;
- exact section types and section features;
- an expanded required-file map containing the existing reviewed byte size + SHA-256 for all six required files.

The payload must contain no local path, timestamp, platform, Python/environment, or machine-specific state. Repeated calls must be equal and caller mutation must not mutate authoritative constants.

Expected RED: no public fingerprint function exists yet.

### GREEN

- Promote the existing section-schema constants and required-feature inventory to explicit reviewed constants in `cuc_index.py`.
- Add one canonical payload constructor next to the verifier/constants.
- Build the payload only from the already-enforced reviewed constants; do not recompute compatibility from generated Burns output.
- Keep the existing byte/count/section validator unchanged except to consume the same public reviewed constants where appropriate.

## Slice 2 — module metadata/report projection

### RED

Extend synthetic module tests to require:

- existing scalar metadata keys `cucRepository`, `cucCommit`, `cucVersion`, `cucManifestSha256` remain unchanged;
- every Burns feature additionally carries deterministic compact structural metadata:
  - `cucCompatibilitySchema`;
  - `cucRequiredFeatures`;
  - `cucNodeTypeCounts` as canonical JSON;
  - `cucSectionTypes`;
  - `cucSectionFeatures`;
- `burns-module-report.json` / `build_burns_module_report()` exposes the complete canonical fingerprint, including expanded required-file fingerprints;
- changing one central reviewed structural constant changes both metadata and report projections together, proving there is one source of truth rather than duplicated literals.

Expected RED: current module metadata/report contain only the four-field identity.

### GREEN

- Remove `module.py`'s private duplicated four-field compatibility constructor.
- Import/use the public canonical fingerprint constructor from `cuc_index.py`.
- Keep `_compatibility_payload(index)` as the exact reviewed-identity guard, but return/project the canonical full fingerprint only after the supplied index identity matches the reviewed repository/commit/version/manifest digest.
- Derive compact feature-header strings from that same payload.
- Preserve existing report schema/version and existing identity keys for backward compatibility; extend `cuc_compatibility` rather than replacing it with an incompatible object.

## Slice 3 — documentation

Update README with a compact `CUC compatibility fingerprint` subsection that documents:

- exact reviewed repository/commit/version;
- relied-on CUC features and structural/navigation assumptions;
- reviewed node counts and section schema;
- compact feature-header vs expanded report representation;
- deliberate review procedure for any future CUC update.

Do not duplicate all six file hashes in README; the generated report and `cuc_index.py` remain the detailed source.

## Regression gates

Run the full existing suite on Python 3.10/3.12/3.13 plus the Agora and Context-Fabric contract jobs. Existing reviewed-CUC rejection tests must stay green, especially byte fingerprint, node-count, section-schema, symlink, and module-composition checks.

No Burns-derived source or generated module artifact is committed.

## Independent adversarial review

Freeze one exact final head and independently challenge:

- duplicated compatibility literals drifting between verifier, TF headers, and report;
- accidental weakening from exact CUC identity to version-only compatibility;
- missing `sign`/word/line/column/tablet counts or incorrect required-feature inventory;
- confusing required files with loaded Text-Fabric source features;
- noncanonical ordering/JSON causing nondeterministic module bytes;
- mutation of returned payload altering global reviewed constants;
- local paths/environment/timestamps leaking into durable compatibility metadata;
- report/header backward compatibility;
- accidental inclusion of CUC/Burns payload data or changes to annotation/node placement.

Merge only after exact-head CI is green and the commit-anchored independent review has no blocker.
