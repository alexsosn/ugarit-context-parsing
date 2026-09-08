# Research: reject symlinked source roots (#10)

## Question

Do the current CSV/PDF loaders honor the repository's declared `allow_symlinks: false` contract when the **supplied source directory itself** is a symlink, and what is the narrowest fix that preserves valid-source semantics?

## Baseline

Baseline is `master@b7a7f00c6aeba1745eb674c46622d66f1681002d`.

Relevant paths:

- `src/ugarit_context_parsing/source.py::load_csv_directory`
- `src/ugarit_context_parsing/pdf_source.py::load_pdf_directory`
- shared `_reject_symlinks()` in `source.py`
- `agora.materializer.json`, where both materializers declare `input.allow_symlinks: false`
- existing descendant-symlink regressions in `tests/test_tf_materializer.py` and `tests/test_pdf_materialization.py`

## Current behavior

Both loaders begin by resolving the input:

```python
source_root = Path(root).resolve()
```

Only after that do they call `_reject_symlinks(source_root)`.

`Path.resolve()` dereferences a symlink in the supplied final path component. Consequently, if `root-link -> real-root`, the loader validates and scans `real-root`; `_reject_symlinks()` can no longer observe that the caller supplied `root-link`.

Descendant symlinks remain rejected because `_reject_symlinks()` recursively inspects entries beneath the resolved source root and calls `is_symlink()` on those entries.

Thus the current behavior is asymmetric:

- real source root: accepted;
- symlink inside the source tree: rejected;
- supplied source-root entry itself is a symlink: accepted.

That is inconsistent with the manifest's fail-closed statement that symlinks are not allowed for either materializer.

## Scope boundary

The narrow contract for this ticket is the directory entry directly supplied as `root`.

Do **not** reject arbitrary symlinks in ancestor path components. For example, if `/mount/current/project/source` traverses a symlinked mount or parent directory but the supplied `source` entry itself is a real directory, ancestor policy belongs to the host/runtime filesystem boundary rather than this corpus loader. Walking and rejecting every ancestor would be a wider, platform-sensitive contract not established by the existing manifest/tests.

Do not alter path normalization after acceptance: once the supplied root entry is verified not to be a symlink, resolving it remains useful for stable relative-path computation and for the existing source model.

## Nonexistent and dangling inputs

A dangling symlink supplied as the source root is still a symlink and should fail with the symlink-specific validation error before the generic "source directory does not exist" error. This is fail-closed and makes the trust-boundary failure explicit.

A normal nonexistent path should retain the existing `source directory does not exist` behavior.

Relative paths and paths containing `.` / `..` should retain existing behavior. The direct supplied path object can be checked with `is_symlink()` before `.resolve()`; after that, the resolved path is used as today.

## TOCTOU boundary

A check-before-resolve sequence cannot defend against an adversary concurrently replacing filesystem entries between the check and later reads. The materializer is designed for a user-selected local static source tree, not for hostile concurrent mutation. Eliminating filesystem TOCTOU completely would require descriptor-relative/openat-style traversal and is outside this ticket.

The existing source-immutability/determinism evidence remains relevant for non-concurrent inputs.

## Minimal implementation shape

Introduce a small shared helper in `source.py`, for example:

```python
def _resolve_source_root(root: str | Path) -> Path:
    supplied = Path(root)
    if supplied.is_symlink():
        raise SourceValidationError("source root must not be a symlink")
    source_root = supplied.resolve()
    if not source_root.is_dir():
        raise SourceValidationError(f"source directory does not exist: {root}")
    return source_root
```

Both CSV and PDF loaders should call this helper, then run the existing `_reject_symlinks(source_root)` unchanged.

This centralizes the trust-boundary rule and avoids duplicating two subtly different checks.

## TDD decision

A real behavioral defect exists and is directly testable. Preserve RED before production change.

Add one focused CSV test and one focused PDF test that:

1. create a real source directory containing otherwise-valid synthetic input;
2. create a sibling symlink whose target is that real source directory;
3. call the corresponding loader with the symlink path itself;
4. require `SourceValidationError` matching `symlink`.

On the current implementation both tests should fail because the loaders accept the symlinked root. Existing real-root and descendant-symlink tests remain the non-regression controls.

Skip only if symlink creation is genuinely unavailable on the platform.

## Semantics/provenance impact

For valid real roots, no scholarly or Text-Fabric semantics change:

- same files are selected;
- same sorted relative paths are used;
- same source bytes are parsed;
- same `tree_sha256` algorithm is used;
- no absolute path is added to graph/report output;
- CSV/PDF determinism evidence remains valid.

The change only converts an input previously accepted contrary to policy into an explicit validation failure.

## Gates

Final exact head must pass:

- full Python 3.10 / 3.12 / 3.13 test matrix;
- installed-package verification outside checkout;
- execution-environment evidence step in all matrix cells;
- pinned Agora manifest-contract job;
- fresh logically independent adversarial review.
