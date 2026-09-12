# Issue 62 plan: exact ownership for existing Burns module output

Research: `research/issue-62/RESEARCH.md`.

## Phase 1 — preserved RED

Add focused tests only on top of reviewed #55; production remains unchanged.

Required cases:

1. Existing `burns_custom.tf` plus an otherwise valid prior Burns module/report must be rejected before Fabric construction; every existing byte remains unchanged.
2. Existing foreign `foreign.tf` remains rejected (regression control).
3. A complete genuine prior module with exactly the six reviewed TF files plus valid report remains replaceable transactionally.
4. Exact six TF files without report fail closed before Fabric.
5. Valid report with one reviewed feature missing fails closed before Fabric.
6. Malformed/foreign report identity fails closed before Fabric.
7. A fake Fabric/save hook that adds `burns_custom.tf` to the live output during staging must cause final publication validation to reject before any existing module file is moved.
8. Mid-publication rollback of a genuine exact prior module remains byte-for-byte correct.

Expected RED: #55 rejects symlinks/non-`burns_` TF, but accepts unknown regular `burns_custom.tf` and `_publish()` wildcard-adopts/removes it.

## Phase 2 — GREEN

In `module.py` only:

- add a strict reader for existing `burns-module-report.json` top-level ownership identity;
- make `_validate_existing_module_output(output)` return the exact tuple of owned paths;
- require existing TF filenames to equal `_EXPECTED_TF_FILES` exactly when any module artifact exists;
- require valid report schema, feature inventory, and exact reviewed CUC compatibility;
- reject report-only/TF-only/partial/extra/malformed states;
- remove prefix-based ownership authorization;
- change `_publish()` to perform final live validation immediately before first mutation and to move only the exact owned paths returned by that validator;
- preserve #55 `prepare_output_root` and symlink checks;
- preserve exact staged inventory validation and transactional rollback.

Do not change module schema, features, CUC fingerprint, node payloads, CLI, package version, manifest, or legacy writer.

## Phase 3 — exact-head gates

Because this is the primary module writer, require on one frozen head:

- Python 3.10 / 3.12 / 3.13 + installed-package smoke;
- Agora contract;
- reviewed-CUC exact integration;
- generic Context-Fabric contract;
- real reviewed-CUC + Burns feature module through cfabric-mcp.

## Phase 4 — independent adversarial review

Challenge from scratch:

- whether arbitrary prefix-matching files can still be deleted;
- whether a forged/minimal report can authorize deletion too easily;
- report-only, partial and exact-inventory semantics;
- race between post-stage validation and publication;
- whether `_publish()` reintroduces wildcard discovery;
- rollback restoration and unrelated non-TF preservation;
- symlink protections from #55;
- future-schema/stale-feature handling is explicit fail-closed rather than heuristic;
- no data/runtime/schema changes outside publication ownership.

Any material finding gets a review-derived RED before correction.

## Phase 5 — merge ordering

This branch is stacked on #61. Keep draft/unmerged until GitHub Release `v0.3.0` exists at exact `4994a45c53a73c09a4939731bc56af585b3ba30a`, then merge prerequisite stack in order (#60 → #61 → #62), refreshing/retesting if bases change.
