# Issue 56 plan: reject source/output overlap

Research: `research/issue-56/RESEARCH.md`.

## Phase 1 — preserved RED

Add synthetic CLI tests only. Production remains unchanged.

Required cases:

1. `convert`: output exactly equals loaded source root → reject before `write_artifact`.
2. `module`: output exactly equals loaded source root → reject before CUC index/alignment/module writer.
3. output nested under source → reject.
4. source nested under output → reject.
5. output spelling through a symlinked ancestor resolves into the source tree → reject where symlinks are available.
6. sibling/disjoint output → preserve current success path and exact caller `Path` handed to the writer.

Prefer a small synthetic `WorkbookSource` returned by a patched `_load_source()` so these tests exercise only orchestration/path policy and do not duplicate CSV/PDF parsing tests.

Expected RED: current CLI has no source/output topology validation, so overlapping cases continue into downstream graph/module work or writers.

## Phase 2 — GREEN

In `cli.py` add a private pure helper, for example:

```python
def _validate_source_output_disjoint(source_root: Path, output: Path) -> None:
    canonical_source = source_root.resolve(strict=False)
    canonical_output = output.resolve(strict=False)
    if (
        canonical_source == canonical_output
        or canonical_source.is_relative_to(canonical_output)
        or canonical_output.is_relative_to(canonical_source)
    ):
        raise SystemExit(...)
```

Call it immediately after `_load_source()` in both `_run_module()` and `_run_convert()`.

Constraints:

- use returned `WorkbookSource.root` rather than independently reinterpreting the original source argument;
- do not create directories during validation;
- do not resolve/rewrite the `args.output` object passed to the writer after successful validation;
- keep source validation errors unchanged;
- do not add CUC/output checks;
- do not modify low-level writers, source loaders, graph/alignment behavior, package version, or manifests.

## Phase 3 — exact-head CI

Run one frozen head through:

- Python 3.10 / 3.12 / 3.13;
- installed-package smoke;
- Agora contract;
- generic Context-Fabric consumer contract;
- reviewed-CUC/module integration workflows if their path triggers include `cli.py` / the new test.

## Phase 4 — logically independent adversarial review

Review from scratch and challenge:

- equality vs both ancestry directions;
- relative paths, `..`, and existing symlinked ancestors;
- preservation of sibling paths;
- whether rejection occurs before expensive/destructive module/CUC/writer work;
- whether writer receives the caller's original output spelling for disjoint paths;
- interaction with source-root leaf-symlink validation and #55 publication-time output checks;
- accidental widening into CUC/output policy or direct-writer API semantics.

Any material finding must get a separate review-derived RED before correction.

## Phase 5 — merge ordering

Keep the PR draft/unmerged while `master` remains frozen for first-release publication. Do not merge before GitHub Release `v0.3.0` exists and resolves to exact commit `4994a45c53a73c09a4939731bc56af585b3ba30a`.