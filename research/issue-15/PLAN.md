# Issue 15 plan: MIT software license

## Scope

Add an explicit MIT software license without changing Burns source/data terms, converter behavior, package version, Agora materializer version, or release state.

## Phase 1 — preserved RED

Add `tests/test_software_license.py` only.

The tests must require:

1. repository `LICENSE` exists and contains the standard MIT grant/disclaimer plus the 2026 copyright notice;
2. installed package Core Metadata reports `License-Expression: MIT`;
3. installed package Core Metadata includes `LICENSE` in `License-File`;
4. README clearly identifies repository software as MIT licensed;
5. README separately preserves Burns CC BY-NC-ND 2.5 source terms and the non-redistribution warning for generated Burns-derived CSV/TF artifacts.

The RED must fail because the license file/metadata/software wording are absent, while all pre-existing project tests remain green.

## Phase 2 — GREEN implementation

Make only these changes:

- add standard `LICENSE` MIT text;
- add `license = "MIT"` and `license-files = ["LICENSE"]` to `[project]` in `pyproject.toml`;
- revise README licensing text to explicitly separate software, Burns source material and generated Burns-derived artifacts.

Do not modify source/parser/module code or `agora.materializer.json` in this ticket.

## Phase 3 — package evidence

Run the normal Python 3.10/3.12/3.13 matrix. The installed-package step and the new tests must prove the generated package metadata, not merely the source TOML text.

Existing Agora, reviewed-CUC and Context-Fabric contracts must remain green where triggered. No Burns-derived artifact may be generated/uploaded as release material.

## Phase 4 — adversarial review

Freeze the final head and review independently for:

- accidental application of MIT wording to Burns data;
- any modification of the standard MIT text;
- package metadata disagreement with `LICENSE`;
- missing license file from built package metadata;
- version/release/manifest changes leaking into this ticket;
- copied/vendor code notices that would need preservation.

Any blocker gets a regression/fix/retest before a fresh exact-head review.

## Completion

After merge, close #15. #16 becomes unblocked for SemVer/version alignment and the first stable GitHub release.
