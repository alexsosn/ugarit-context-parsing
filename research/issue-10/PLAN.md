# Plan: reject symlinked source roots (#10)

## Goal

Make both CSV and PDF materializers fail closed when the caller supplies a symlink as the source-root directory, matching the existing `allow_symlinks: false` manifest contract, without changing semantics for valid real directories.

## Preconditions

- Research: `research/issue-10/RESEARCH.md`.
- Baseline: `master@b7a7f00c6aeba1745eb674c46622d66f1681002d`.
- Existing descendant-symlink rejection must remain unchanged.
- No scholarly normalization, graph, report, writer, or manifest change is expected.

## RED slice

Before production code changes, add focused tests to the existing loader test modules.

### CSV RED

In `CsvSourceTests`:

1. create a real directory containing one valid one-level Workbook CSV;
2. create a sibling symlink whose target is that real source directory;
3. call `load_csv_directory()` with the symlink path itself;
4. require `SourceValidationError` whose message contains `symlink`.

### PDF RED

In `PdfSourceTests`:

1. create a real directory containing one one-level synthetic `.pdf` file;
2. use the existing injected fake parser so PDF binary validity is irrelevant to this narrow loader test;
3. create a sibling symlink to the real source directory;
4. call `load_pdf_directory(link, parser=fake_parser)`;
5. require the same symlink validation failure.

Both tests may skip only when `Path.symlink_to()` is unavailable on the platform.

At the RED head, production files must be unchanged. Exact-head CI should fail because both loaders currently resolve the root symlink and accept its target.

## GREEN slice

Add one shared private helper in `source.py` that validates the supplied root entry **before** resolving it.

Required behavior:

- `Path(root).is_symlink()` => `SourceValidationError` mentioning `symlink`;
- otherwise resolve the path;
- resolved non-directory => retain the existing `source directory does not exist: ...` error;
- return the resolved real directory.

Use the helper from both `load_csv_directory()` and `load_pdf_directory()`.

Keep `_reject_symlinks(source_root)` unchanged so descendant symlinks continue to be rejected independently.

Do not inspect/reject arbitrary ancestor path components. Do not change source-tree hashing, relative path derivation, parser behavior, graph semantics, reports, or publication.

## Regression checks

The full suite must continue proving:

- ordinary real CSV roots load successfully;
- ordinary real PDF roots load successfully;
- descendant CSV/PDF symlinks remain rejected;
- nonexistent real paths keep the existing missing-directory error;
- determinism replay tests remain green for CSV and PDF;
- Agora manifest remains unchanged and valid.

## Exact-head gates

Require the normal CI matrix on the final head:

- Python 3.10;
- Python 3.12;
- Python 3.13;
- installed-package verification outside checkout;
- execution environment recording in every test job;
- pinned Agora manifest-contract validation.

## Independent adversarial review

Freeze the final head and review without relying on the implementation rationale. Challenge at least:

1. Can a symlink supplied as the final source-root path still be dereferenced before validation?
2. Are CSV and PDF paths using exactly the same shared rule?
3. Are descendant symlinks still rejected?
4. Did the fix accidentally reject normal directories reached through symlinked ancestor components?
5. Did nonexistent-path behavior change unintentionally?
6. Can valid source semantics/tree hashes change because of the helper?
7. Is the error fail-closed for dangling root symlinks?
8. Did any production surface outside source validation change unnecessarily?

Any blocker starts a focused regression sub-loop and requires a new exact-head test/review cycle.

## Definition of done

- research precedes plan;
- tests-only RED is preserved and fails for the intended accepted-root-symlink behavior;
- minimal shared source-root validation makes both tests GREEN;
- full exact-head CI passes;
- fresh logically independent adversarial review finds no blocker;
- PR merges and closes #10.
