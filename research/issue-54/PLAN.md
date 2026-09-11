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

Tests should use synthetic data only and must not include Burns-derived source payloads.

## Phase 2 — GREEN implementation

Change only `src/ugarit_context_parsing/writer.py` plus tests/research docs.

Add small private helpers:

- `_allowed_tf_names(data: TFData) -> frozenset[str]`
  - node feature names + edge feature names + `otext.tf`.
- `_read_existing_burns_report(path: Path) -> dict | None`
  - reject symlinks;
  - parse UTF-8 JSON;
  - return only a strict successful legacy Burns report shape; otherwise signal invalid ownership.
- `_validate_existing_output(output: Path, data: TFData) -> tuple[Path, ...]`
  - reject symlinked candidate TF/report files;
  - permit empty/nonexistent output;
  - preserve unrelated non-TF files;
  - require valid report + required warp files when TF files exist;
  - reject any TF name outside `_allowed_tf_names(data)`;
  - reject report-only/incomplete/invalid prior artifacts;
  - return exactly the recognized prior owned paths that may be moved to backup.

Call this preflight before `_make_fabric` / staging so a known foreign output does not waste conversion work.

Refactor `_publish(stage, output, old_owned)` so it never performs a wildcard ownership decision. It receives the preflight-proven owned paths and moves only those plus the validated report.

Do not change graph shape, report schema/version, CLI syntax, primary module writer, Agora manifest, package version, or licensing.

## Phase 3 — test gates

On the final frozen branch head run the normal repository CI:

- Python 3.10;
- Python 3.12;
- Python 3.13;
- installed-package smoke;
- Agora contract;
- Context-Fabric consumer contract.

No new network/data workflow is needed because all new tests are synthetic filesystem tests.

## Phase 4 — logically independent adversarial review

Review the final exact head from scratch and challenge:

- can a foreign TF directory still be modified before rejection?
- can a forged/partial/invalid `conversion-report.json` accidentally grant ownership?
- are unknown `.tf` files ever deleted merely by suffix?
- can a valid prior Burns artifact still be replaced?
- does rollback restore old files after a failure during installation rather than only a failed Fabric save?
- do symlinked candidate files bypass ownership checks?
- are unrelated non-TF files preserved?
- did the patch accidentally widen into #55/#56/#57 or alter module architecture?

Any review finding that changes behavior requires a focused review-derived RED before the fix.

## Phase 5 — merge ordering

Keep the PR draft/unmerged until GitHub Release `v0.3.0` exists at exact commit `4994a45c53a73c09a4939731bc56af585b3ba30a`. After publication, refresh base if needed and rerun exact-head CI before merge.
