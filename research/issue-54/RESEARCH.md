# Issue 54 research: legacy writer output ownership safety

## Scope

This issue fixes one concrete destructive behavior in the deprecated standalone `convert` writer: successful publication currently removes every existing `*.tf` file from `--output`, regardless of whether that file belongs to a prior Burns artifact.

The frozen release candidate remains `master@4994a45c53a73c09a4939731bc56af585b3ba30a`; this branch is post-release work and must not be merged before `v0.3.0` is published at that exact commit.

## Current behavior

`src/ugarit_context_parsing/writer.py::_publish()` gathers all regular files matching `output.glob("*.tf")`, moves them to a temporary backup, installs the staged Burns files, and deletes the backup when publication succeeds. Therefore an output directory containing a foreign Text-Fabric corpus can be replaced merely because its files end in `.tf`.

`tests/test_materialization.py::test_successful_publication_replaces_tf_set_and_report_together` currently encodes this unsafe behavior by creating `stale.tf` and asserting that it disappears after a successful write. `stale.tf` is not a known Burns feature and must no longer be treated as owned.

The primary CUC-aligned module writer is already more conservative: it rejects existing non-Burns TF files instead of deleting them. #54 brings the legacy compatibility path to the same user-data safety principle without changing its data model.

## What counts as a prior Burns standalone artifact

Filename suffix alone is not evidence of ownership. The legacy writer already emits two independent signals that can be combined conservatively:

1. `conversion-report.json` with schema/version/status metadata. A successful prior Burns report has:
   - `schema_version == 1`;
   - `converter.name == "ugarit-context-parsing"`;
   - a non-empty converter version string (historical versions must remain acceptable);
   - `source.format` equal to `csv` or `pdf`;
   - a 64-character lowercase hexadecimal source-tree SHA-256;
   - a positive source file count;
   - a mapping of checks whose values are all true;
   - `status == "ok"`.
2. A fixed Text-Fabric file inventory owned by the legacy Burns producer. The inventory is derived from `build_tf_data()`'s stable feature contract, not from a caller-supplied `TFData` instance. It contains the legacy node features (`otype`, source provenance, Burns fields, language/navigation labels), `oslots`, and `otext`. At minimum, `otype.tf`, `oslots.tf`, and `otext.tf` must be present.

The report producer version is intentionally *not* required to equal the current package version. Research found that `build_conversion_report()` still records `0.2.0` while the release candidate package/manifest is `0.3.0`; this metadata question is tracked separately in #57.

The report is an accidental-overwrite ownership marker, not a cryptographic authentication mechanism against a malicious local user who can already edit/delete their own files. The fixed producer inventory prevents the direct API caller from widening ownership merely by adding arbitrary feature names to `TFData`.

## Fail-closed ownership rule

Before constructing/staging a new artifact, inspect the output directory if it already exists.

- Empty/nonexistent output: allowed.
- Existing unrelated non-TF files: preserved and ignored, as today.
- Existing `conversion-report.json` without any TF files: reject as ambiguous rather than overwrite an unrelated report.
- Existing TF files without a valid Burns report: reject.
- Existing TF files plus a valid Burns report, but missing one of `otype.tf`, `oslots.tf`, `otext.tf`: reject as incomplete/ambiguous.
- Existing TF files plus a valid Burns report, but any TF filename outside the fixed legacy producer inventory: reject; never silently delete the extra file.
- Existing TF files plus a valid Burns report and only fixed producer-owned filenames with the warp files present: recognize as a prior Burns artifact and permit transactional replacement.
- Symlinked artifact files/report are ambiguous and must be rejected for this ownership decision. Output-root symlink policy for both writers is a separate cross-writer ticket (#55).

Once preflight has proven ownership, publication may move only the recognized existing Burns TF files and `conversion-report.json` into the rollback backup. It must never glob-and-own arbitrary `*.tf` names.

## Transactional behavior

The existing stage/backup/install ordering is sound once ownership is constrained:

1. validate the requested TF feature names against the fixed legacy producer inventory;
2. preflight the existing output before invoking Text-Fabric, so known foreign output is rejected without conversion work;
3. generate all new files in a private temporary stage;
4. validate every staged `.tf` entry against the same fixed inventory and reject unexpected/symlinked stage files;
5. revalidate the live output after staging and immediately before publication, so output changes during a long `Fabric.save()` do not bypass the initial preflight;
6. move recognized prior Burns files/report to a temporary backup;
7. install the validated staged set;
8. on any installation exception, remove newly installed files and restore the complete recognized prior artifact.

A focused mid-publication failure test patches `Path.replace` only for one staged install after at least one new file was installed and verifies restoration of every prior Burns file/report.

## Adversarial review findings

The first GREEN (`7ee3dcf0e7ddd382e33f33c9b3ff03a189ba476d`) passed the complete CI matrix but an independent review found three gaps:

1. allowed ownership was computed from caller-supplied `TFData`, so a direct caller could add `g_cons` and make an existing `g_cons.tf` look owned;
2. output was checked only before `Fabric.save()`, leaving a staging-time race where a newly appearing foreign file could be overwritten;
3. `_publish()` accepted every staged `*.tf`, so an unexpected Fabric-produced feature could escape the intended inventory.

A preserved review-derived RED (`513d2303cc86950b82bffb2af740b8f088dac127`) added one synthetic test for each case. Python 3.12 ran 218 tests and failed exactly those three new adversarial checks while the original #54 safety tests and unrelated suite remained green.

The hardened implementation uses one immutable producer-owned inventory for requested data, existing-output ownership, and staged-output validation, and repeats live-output preflight after staging.

## Source/output overlap

The CLI loads CSV/PDF source records fully before calling the writer, so source/output overlap does not corrupt already-loaded records during the current process. It can still create/replace TF/report files inside the source tree and may become ambiguous with future discovery rules. That broader policy is intentionally separated into #56.

## Output-root symlinks

Both writers currently follow a symlinked output directory through normal `Path.is_dir()` behavior. This is a cross-writer path policy issue, not necessary to prove #54's foreign-TF ownership boundary, and is tracked in #55. #54 only rejects symlinked candidate artifact files/report when deciding whether an existing legacy artifact is owned.

## Security / data boundary

This change does not inspect or redistribute Burns source payloads. It changes only local publication safety. No generated Burns CSV/PDF/TF data belongs in the repository or CI artifacts.
