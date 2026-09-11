# Issue 56 research: source/output topology safety

## Current execution order

Both public materialization paths load the complete source before publication:

- `convert`: `_load_source()` → `build_tf_data()` → report → `write_artifact()`;
- `module`: `_load_source()` → normalization → reviewed CUC index/alignment → module/report → `write_burns_module()`.

Both CSV and PDF loaders use the same `_resolve_source_root()` helper. That helper rejects a symlink supplied as the source-root leaf, resolves the accepted root, and returns the resolved real directory as `WorkbookSource.root`. Both loaders also reject symlinks contained inside the source tree.

Thus after `_load_source()` succeeds, `source.root` is the canonical real source directory for both adapters.

## What overlap can damage today

The writers do not recursively delete an entire source tree, so current CSV/PDF content is already in memory and is not directly destroyed merely because output overlaps source. Nevertheless co-location is unsafe and ambiguous:

- `convert` publishes root-level Text-Fabric files and `conversion-report.json`;
- `module` publishes `burns_*.tf` plus `burns-module-report.json`;
- if output equals source or lies below source, those generated files are written into the user-owned source tree and can replace same-named user files;
- if source lies below output, publication mutates an ancestor of the source tree, coupling generated state and source state and creating an unstable topology for future discovery/cleanup rules.

The fact that today's CSV discovery is only `*/*.csv` and PDF discovery is only `*/*.pdf` is not a sufficient safety contract for intentionally overlapping generated and source trees.

## Policy decision

Reject all source/output ancestry overlap for both public commands:

1. output equals source;
2. output is a descendant of source;
3. source is a descendant of output.

Allow sibling/disjoint trees.

This symmetric rule is easier to reason about than allowing one overlap direction based on today's writer/discovery implementation, and it prevents future changes from turning a previously tolerated topology into destructive behavior.

## Canonical path comparison

Use the already canonical `WorkbookSource.root` for source.

Canonicalize the requested output with:

```python
Path(output).resolve(strict=False)
```

This resolves existing symlinked ancestors and lexically normalizes the non-existing tail without creating it. Therefore aliases such as `linked-parent/output` and `real-parent/output` compare as the same topology while a symlinked ancestor remains otherwise supported.

Python 3.10+ provides `Path.is_relative_to()`, so overlap is:

```python
source == output or source.is_relative_to(output) or output.is_relative_to(source)
```

Do not resolve or mutate the source argument independently before loading: source validation remains owned by the source loaders.

## Enforcement boundary

The best boundary is the CLI orchestration layer immediately after `_load_source()` returns:

- it has the authoritative resolved `WorkbookSource.root`;
- it can reject before graph construction, normalization, CUC loading/alignment, Fabric construction, or output publication;
- it applies identically to CSV/PDF and `convert`/`module`;
- writer APIs remain usable independently with their existing publication contracts.

This ticket protects the supported CLI topology, not arbitrary direct calls to low-level writers.

## Error contract

Raise a user-facing `SystemExit` from CLI orchestration with a stable message containing `source/output paths must be disjoint` and the canonical source/output paths. Do not silently relocate output or rewrite user arguments.

## Symlink / TOCTOU boundary

This topology check detects aliases through symlinked ancestors at the time orchestration validates the paths. It is not a replacement for #55's publication-time output-leaf symlink checks and does not attempt OS-specific directory-handle locking against a malicious concurrent local process.

## CUC boundary

Do not widen this issue to CUC/output topology. CUC is a separate external read-only dependency with its own exact fingerprint contract. If a concrete CUC/output destructive case is found, track it independently.

## Test strategy

Use synthetic temporary directories and patch downstream work so RED/GREEN tests isolate orchestration:

- equality rejected for both `convert` and `module`;
- output nested under source rejected;
- source nested under output rejected;
- alias through a symlinked ancestor rejected where symlinks are available;
- sibling/disjoint output remains allowed and reaches the expected writer;
- module overlap rejection happens before reviewed-CUC indexing/alignment/writer work.

No Burns-derived source data is required.

## Release boundary

This is post-release stability work. Keep the branch off `master` until GitHub Release `v0.3.0` actually exists at frozen release commit `4994a45c53a73c09a4939731bc56af585b3ba30a`.