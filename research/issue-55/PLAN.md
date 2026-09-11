# Issue 55 plan: fail closed on symlinked output roots

Research: `research/issue-55/RESEARCH.md`.

## Phase 1 — preserved RED

Add synthetic tests before production changes.

Required RED cases:

1. **Legacy output leaf symlink**
   - create a real target directory with sentinel content;
   - supply a directory symlink as `output_dir`;
   - `write_artifact()` must raise before Fabric construction/save and leave target bytes unchanged.

2. **Module output leaf symlink**
   - same shape for `write_burns_module()`;
   - no staged/publication work is allowed through the symlink.

3. **Dangling output leaf symlink**
   - both writers must classify it as a symlink violation, not as a nonexistent safe output directory.

4. **Symlinked ancestor remains allowed**
   - create `linked-parent -> real-parent` and use the real leaf `linked-parent/output`;
   - both writers may publish there because the leaf itself is not a symlink.

5. **Staging-time leaf substitution**
   - output starts absent;
   - synthetic Fabric creates `output` as a directory symlink to an external target during `save()`;
   - both writers must re-check after staging, reject, and leave the target unchanged.

6. **Module-owned artifact symlinks**
   - an existing `burns_*.tf` symlink or `burns-module-report.json` symlink is rejected before Fabric;
   - an expected staged Burns feature symlink is rejected before publication.

Keep all tests synthetic and avoid Burns-derived data.

## Phase 2 — GREEN implementation

Add `src/ugarit_context_parsing/publication.py` with a narrow shared helper:

- create the parent directory if necessary;
- reject `output.is_symlink()` before `exists()/is_dir()` handling;
- reject an existing non-directory leaf;
- return the original `Path` without resolving ancestors and without creating the leaf directory.

Legacy writer:

- route `_validate_existing_output()` through the helper so both its pre-Fabric and post-stage checks reject output-root symlinks;
- preserve every #54 ownership/stage/rollback rule unchanged.

Module writer:

- use the helper before Fabric construction;
- reject symlinked existing `burns_*.tf` candidates and report marker;
- validate staged expected feature paths as regular non-symlink files;
- use the helper again after staging/report construction immediately before `_publish()`;
- preserve current exact feature inventory, foreign-TF guard, report integrity checks, and rollback.

Do not resolve output paths, reject symlinked ancestors, alter source validation, or change CLI/version/Agora behavior.

## Phase 3 — exact-head CI

Run the full normal matrix on one frozen head:

- Python 3.10 / 3.12 / 3.13;
- installed-package smoke;
- Agora contract;
- Context-Fabric consumer contract.

## Phase 4 — logically independent adversarial review

Review from scratch and challenge:

- dangling vs valid directory symlink classification;
- whether any Fabric call happens before initial symlink rejection;
- staging-time replacement with a symlink;
- symlinked module-owned existing files/report;
- staged symlink escape;
- preservation of symlinked-ancestor compatibility;
- interaction with #54 second preflight and transactional rollback;
- accidental widening into #56 or parent-ancestry resolution.

Any material finding gets a review-derived RED before correction.

## Phase 5 — stacking / merge ordering

Open the PR against `fix/legacy-writer-foreign-tf-54`, not `master`. Keep it draft while #60 is unmerged. After #60 lands, retarget/rebase as appropriate and rerun exact-head CI/review. Neither PR may merge to `master` before `v0.3.0` exists at `4994a45c53a73c09a4939731bc56af585b3ba30a`.
