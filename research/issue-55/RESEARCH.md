# Issue 55 research: output symlink publication policy

## Stacking / release boundary

This work is stacked on reviewed #54 head `7f5c4a8c41b5a39b13f79eab87f30336bcdc9852` so both legacy-writer safety changes can evolve without creating a later conflict in `writer.py`. Its PR should target `fix/legacy-writer-foreign-tf-54` until #54 lands. Neither PR may reach `master` before `v0.3.0` is published at frozen release commit `4994a45c53a73c09a4939731bc56af585b3ba30a`.

## Current behavior

Both publication paths treat a directory symlink supplied as `--output` like an ordinary directory because `Path.is_dir()` follows the link.

- Legacy `write_artifact()` validates output contents, stages data, and ultimately calls `output.mkdir(..., exist_ok=True)` / `Path.replace()` through the symlink target.
- `write_burns_module()` likewise accepts `output.is_dir()` for a symlink and publishes Burns feature files into the target directory.

Thus the path spelling shown to the user may not be the filesystem directory mutated.

The source loaders already have a deliberate leaf-vs-ancestor policy: a symlink supplied **as the source root itself** is rejected, but a real leaf below a symlinked ancestor is allowed and resolved. `tests/test_source_root_symlinks.py` explicitly preserves this behavior.

## Policy decision

### Reject the output leaf when it is a symlink

Both writers must reject `Path(output_dir).is_symlink()` before invoking Text-Fabric or moving any output file. This includes dangling symlinks, for which `exists()` is false but `is_symlink()` is true.

The same check must happen again after staging and immediately before publication because another process can replace an initially absent/real output leaf with a directory symlink during a long `Fabric.save()` call.

### Allow symlinked ancestors

Do not reject a real output leaf merely because an ancestor path component is a symlink. Reasons:

- this matches the existing source-root policy;
- common OS paths can contain symlinked ancestors (for example platform-specific temporary-directory aliases);
- rejecting every symlink in the resolved ancestry would be a broader portability policy change rather than protection against a misleading `--output` leaf.

The writer should preserve the caller's path spelling rather than silently replace it with a resolved path.

### Existing/staged artifact-entry symlinks

The hardened legacy writer from #54 already rejects symlinked existing TF/report candidates and staged `.tf` entries.

The module writer should receive the same fail-closed behavior:

- any pre-existing `burns_*.tf` candidate that is a symlink is not treated as owned;
- `burns-module-report.json` symlink is rejected;
- a staged expected feature that is a symlink is rejected rather than installed as a dangling/external link;
- staged report is created by our code after feature validation, so no separate report-symlink case exists in normal production staging.

Foreign non-Burns TF files remain governed by the existing module foreign-file guard.

## Shared helper

A small shared publication-path helper is preferable to duplicating subtly different leaf checks in two writers. Proposed private API in a new `publication.py` module:

```python
def prepare_output_root(output_dir: str | Path, *, label: str) -> Path:
    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise ValueError(f"{label} output path is a disallowed symlink: {output}")
    if output.exists() and not output.is_dir():
        raise ValueError(f"{label} output path is not a directory: {output}")
    return output
```

This helper deliberately does not create the output directory itself; staging can complete without mutating a new output path. Publication code creates the directory only after the final post-stage check.

Legacy `_validate_existing_output()` should call the helper, so both its early and post-stage preflights enforce leaf-symlink rejection.

Module `write_burns_module()` should call it before Fabric construction and again after stage validation/report creation, before `_publish()`.

## Transaction and TOCTOU boundary

Repeating the leaf check after staging closes the practical staging-time substitution demonstrated by a synthetic Fabric test. There is inevitably a tiny filesystem race between the last check and individual `replace()` operations unless the application introduces OS-specific directory handles/locking; that would be disproportionate here and would not protect against an arbitrary malicious local process with equal filesystem permissions. This ticket protects normal callers from misleading/accidental output indirection and staging-time substitutions under the tested API boundary.

## Out of scope

- Source/output overlap remains #56.
- Conversion-report version semantics remain #57.
- #54 remains responsible for legacy foreign-TF ownership; #55 must not weaken its fixed inventory or rollback rules.
- No Burns-derived data enters tests or repository artifacts.
