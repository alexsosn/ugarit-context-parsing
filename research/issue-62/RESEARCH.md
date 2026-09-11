# Issue 62 research: exact ownership for existing Burns module output

## Problem

The reviewed #55 head protects module publication from symlinked output roots/files and revalidates the live output after staging. However, `src/ugarit_context_parsing/module.py::_validate_existing_module_output()` still accepts every regular `*.tf` whose name starts with `burns_`, and `_publish()` then backs up/removes every regular `burns_*.tf`.

That means a user-local or third-party file such as `burns_custom.tf` is treated as Burns-owned solely because of a filename prefix and can be silently removed during a successful module refresh.

## Existing module identity

The feature-module v1 contract already has a complete exact inventory:

- `burns_annotations.tf`
- `burns_annotation_ids.tf`
- `burns_semantic_statuses.tf`
- `burns_worksheet_roles.tf`
- `burns_sections.tf`
- `burns_headwords.tf`
- `burns-module-report.json`

`_EXPECTED_TF_FILES` is derived from the six reviewed `FEATURES`. A generated `burns-module-report.json` additionally carries:

- `schema == burns-tf-module-report-v1`;
- `feature_inventory == sorted(FEATURES)`;
- exact `cuc_compatibility == reviewed_cuc_compatibility_payload()`;
- counts/source/alignment inventories.

For output ownership, the top-level report identity plus exact six-file TF inventory is sufficient and materially stronger than a filename prefix. Re-parsing Text-Fabric node payloads from disk merely to decide whether deletion is authorized would duplicate TF parsing and is unnecessary.

## Selected ownership contract

### New/empty output

Allow publication when the output directory does not exist or exists with no `*.tf` files and no `burns-module-report.json`. Unrelated non-TF files remain untouched.

### Existing module replacement

Treat an existing artifact as writer-owned only when all are true:

1. `burns-module-report.json` exists as a regular, non-symlink file;
2. it parses as a JSON object;
3. top-level `schema` is exactly `burns-tf-module-report-v1`;
4. `feature_inventory` equals `sorted(FEATURES)` exactly;
5. `cuc_compatibility` equals the exact current reviewed CUC compatibility payload;
6. existing regular TF filenames equal `_EXPECTED_TF_FILES` exactly;
7. all six TF entries are regular non-symlink files.

Any report-only, TF-only, partial, extra, unknown, malformed, symlinked, or foreign state fails closed before Fabric construction or publication.

This deliberately does **not** support guessed stale feature inventories. If a future module schema changes the feature set, compatibility with the previous module schema must be researched and encoded explicitly instead of authorizing deletion by `burns_` prefix.

## Unknown regular files

A regular `burns_custom.tf` is never owned merely because of its prefix. Its presence makes the TF inventory differ from the reviewed six-file set and publication must refuse without modifying any bytes.

A non-Burns `foreign.tf` is the same class of failure; ownership is exact-inventory based, not prefix based.

## Report-only and incomplete output

A report without all six expected TF files is incomplete/ambiguous and must be rejected. Likewise exact TF files without a valid module report do not prove ownership.

## Stage-time and live-output races

#55 already revalidates output after staging. #62 should strengthen the publication boundary so the exact ownership function returns the owned paths and `_publish()` consumes that result rather than re-discovering `burns_*.tf` with a wildcard.

`_publish()` should perform the final live validation itself immediately before the first mutation. Therefore a test/fake that adds `burns_custom.tf` during staging is rejected at publication time before backup/install starts.

Even if an uncooperative concurrent actor writes a new unknown file after that final check, `_publish()` must never wildcard-delete it: only the exact paths returned by the ownership validator may be moved. This turns the residual microscopic filesystem race into non-deletion rather than accidental ownership.

## Transactionality

Keep #27/#55 transaction semantics:

- new output is staged first;
- final existing-output validation happens before mutation;
- exact owned old module files/report move to backup;
- exact staged reviewed files/report install;
- an exception rolls installed files back and restores the old exact module.

## Symlink interaction

This branch is intentionally stacked on reviewed #55 head `df6f26b0dbb70619a0dd5caa1c09b2e8caf5404e`. Its output-root, existing-entry, staged-entry, and staged-report symlink checks remain authoritative. #62 only narrows regular-file ownership.

## Merge ordering

Post-release stack: `v0.3.0` publication → #60 legacy ownership → #61 symlink output safety → #62 exact module ownership. Do not merge this branch before those prerequisites land in order.
