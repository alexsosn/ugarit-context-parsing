# Issue 55 adversarial finding: staged report symlink

Independent review of GREEN head `80d537b96710d856cc3bf70a21b017dc92b476d5` found one remaining publication escape inside the existing #55 scope.

The module writer validates every staged `*.tf` entry for symlinks, then unconditionally executes:

```python
(stage / REPORT_FILE).write_text(...)
```

The research assumption that the report is therefore always "created by our code" is too strong. The Fabric adapter receives the same private stage directory and can leave a pre-existing `burns-module-report.json` entry there. If that entry is a symlink, `Path.write_text()` follows it and writes the report payload to an external target before publication validation runs.

This is not an argument that a malicious in-process `fabric_factory` can be sandboxed; it is a fail-closed filesystem contract analogous to the already tested staged feature symlink case. A buggy/custom Fabric implementation must not turn an unexpected staged symlink into an external write merely because its name is the module report rather than a `.tf` feature.

## Review-derived RED

Before changing production, add one synthetic test in a separate adversarial test module:

1. patch `_validate_module_for_write` so the test isolates publication mechanics;
2. use a Fabric stub that writes all six expected Burns `.tf` files as regular files and creates `burns-module-report.json` as a symlink to an external sentinel file;
3. call `write_burns_module()` with a previously absent output directory;
4. require a `ValueError` mentioning `symlink`;
5. require the external sentinel bytes to remain unchanged;
6. require the output directory to remain absent.

Expected RED on `80d537b9...`: current code validates the six `.tf` files, follows the report symlink during `write_text()`, mutates the external sentinel, and does not raise the required symlink error.

## Narrow GREEN

Immediately before writing the staged report, reject `report_stage.is_symlink()` and reject any existing non-regular report entry. Do not change feature inventory, output ownership, alignment/report schemas, or the accepted symlinked-ancestor policy.

After GREEN, rerun the complete exact-head matrix and restart the final independent review from the new SHA.