# Issue 54 plan: fail-closed legacy output ownership

Research: `research/issue-54/RESEARCH.md`.

## Phase 1 — preserved RED

Add focused tests before production changes. The RED must demonstrate the current destructive behavior and the desired ownership boundary without changing unrelated module behavior.

Required RED cases:

1. **Foreign TF corpus is rejected and untouched**
   - pre-create `otype.tf`, `oslots.tf`, `otext.tf`, and a foreign feature such as `g_cons.tf` with sentinel bytes;
   - no valid Burns `conversion-report.json`;
   - `write_artifact(...)` must raise `ValueError` before publication and every sentinel byte must remain unchanged;
   - the fake Fabric writer should not be invoked once foreign ownership is known.

2. **Unknown extra TF in an otherwise prior Burns artifact is rejected**
   - first create a valid Burns artifact through `write_artifact`;
   - add `foreign.tf` with sentinel bytes;
   - second write must raise and leave the complete prior artifact plus `foreign.tf` unchanged.

3. **Recognized prior Burns artifact remains replaceable**
   - create a valid artifact through the writer;
   - mutate one owned file/report to old sentinel content only where the report remains a valid Burns ownership marker;
   - second successful write replaces the owned set while preserving unrelated non-TF files.

4. **Mid-publication rollback restores the prior Burns artifact**
   - start from a recognized prior Burns artifact;
   - patch `Path.replace` to fail during staged installation after at least one staged file has moved;
   - assert every previous owned TF file and `conversion-report.json` is restored byte-for-byte and no partial new file remains.

5. **Ambiguous report-only/incomplete artifact is rejected**
   - a report collision without TF, an invalid report, or missing required warp file must fail closed.

Tests use synthetic data only and contain no Burns-derived source payloads.

Preserved causal RED head: `dc2c6c1e0f513f03bac1b900e3e19ef081ce70a2`. Python 3.10 ran 215 tests: exactly six new ownership assertions failed, while recognized replacement and mid-publication rollback guards already passed and unrelated tests remained green.

## Phase 2 — initial GREEN

Change only `src/ugarit_context_parsing/writer.py` plus tests/research docs.

The first implementation:

- validates an existing successful Burns conversion report;
- rejects report-only/incomplete/symlinked/unknown TF output;
- performs preflight before `Fabric.save()`;
- passes an explicit preflight-owned path tuple into `_publish()` rather than globbing arbitrary `*.tf` files;
- preserves transactional rollback and unrelated non-TF files.

The old materialization test that treated arbitrary `stale.tf` as owned is replaced with a valid prior-Burns replacement test.

Initial GREEN head `7ee3dcf0e7ddd382e33f33c9b3ff03a189ba476d` passed Python 3.10/3.12/3.13, installed-package smoke, Agora, and Context-Fabric contracts.

## Phase 2b — adversarial review-derived RED

Do not accept the first GREEN merely because CI is green. Review it independently from the ownership threat model.

The review found three gaps:

1. existing-output allowlist was derived from caller-supplied `TFData`; a direct API caller could add an arbitrary feature name and widen which pre-existing files counted as owned;
2. existing output was checked only before staging, so a file appearing during `Fabric.save()` could bypass preflight and be overwritten;
3. every staged `*.tf` file was accepted, so unexpected Fabric output was not constrained by the producer contract.

Preserve `tests/test_legacy_writer_output_safety_adversarial.py` before fixing these. Required review-derived RED cases:

- caller-supplied `g_cons` cannot make a foreign `g_cons.tf` owned;
- output is revalidated after staging before any publication mutation;
- an unexpected staged `foreign.tf` is rejected without creating/changing output.

Review-derived RED head: `513d2303cc86950b82bffb2af740b8f088dac127`. Python 3.12 ran 218 tests and failed exactly these three new checks; the original #54 tests were green.

## Phase 2c — hardened GREEN

Use one immutable legacy producer inventory, matching `build_tf_data()`'s known node features plus `oslots.tf` and `otext.tf`. Caller-supplied data may use only names from this inventory; it cannot enlarge ownership.

- Validate requested feature names before preflight/Fabric construction.
- Validate existing output against the immutable inventory and strict successful report marker.
- Validate every staged TF entry against the immutable inventory, reject symlinks/non-files/unexpected names, and require warp files.
- After successful staging, repeat existing-output validation immediately before transactional publication and use this fresh owned-path result.
- Pass the already validated staged map to `_publish()` rather than re-globbing it.
- Keep report producer version compatibility broad enough for genuine older Burns artifacts; #57 owns version-alignment policy.

Do not change graph shape, report schema/version, CLI syntax, primary module writer, Agora manifest, package version, or licensing.

## Phase 3 — final test gates

On the final frozen branch head run the normal repository CI:

- Python 3.10;
- Python 3.12;
- Python 3.13;
- installed-package smoke;
- Agora contract;
- Context-Fabric consumer contract.

No new network/data workflow is needed because all new tests are synthetic filesystem tests.

## Phase 4 — logically independent final adversarial review

Review the final exact head from scratch and challenge:

- can a foreign TF directory still be modified before rejection?
- can caller-supplied data expand the fixed ownership inventory?
- can a partial/invalid ownership report accidentally grant ownership? (The marker is accidental-overwrite protection, not authentication against a malicious local user.)
- are unknown `.tf` files ever deleted merely by suffix?
- is the output checked again after staging?
- can unexpected/symlinked staged files be published?
- can a valid prior Burns artifact still be replaced?
- does rollback restore old files after a failure during installation rather than only a failed Fabric save?
- are unrelated non-TF files preserved?
- did the patch accidentally widen into #55/#56/#57 or alter module architecture?

Any new review finding that changes behavior requires another focused review-derived RED before the fix.

## Phase 5 — merge ordering

Keep the PR draft/unmerged until GitHub Release `v0.3.0` exists at exact commit `4994a45c53a73c09a4939731bc56af585b3ba30a`. After publication, refresh base if needed and rerun exact-head CI before merge.
