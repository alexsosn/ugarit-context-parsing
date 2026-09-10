# Preserved RED: public CUC-aligned Burns module CLI (#43)

Exact RED head: `b60a230cd7a830c79c8c9f893b7ea343e7b02bdd`.

Workflow: `Tests`, run `34415101582`, job `102678128071` (`test (3.12)`).

CI provenance proved the tested pull-request merge used base `30fa9df80e4fee2d3e49a612c76dc0d3900c946c` and exact head `b60a230cd7a830c79c8c9f893b7ea343e7b02bdd`. The environment was CPython 3.12.14 on Ubuntu 24.04 / Linux x86_64 with the resolved package closure recorded by the workflow.

The RED is causal and isolated to the new contract:

- the unchanged generic Context-Fabric/cfabric-mcp consumer contract passed on this head;
- all 190 pre-existing repository tests reached in the full suite passed;
- the six newly added `test_module_cli.ModuleCliTests` produced exactly 3 failures + 3 errors.

Observed failures:

1. CSV module execution: `argparse.ArgumentError: argument command: invalid choice: 'module' (choose from convert)` -> `SystemExit: 2`.
2. PDF module execution: same missing-subcommand failure.
3. Required-`--cuc` parser contract cannot be exercised because `module` is not a recognized subcommand.
4. Top-level help is `usage: ... {convert} ...` and lacks `module` / CUC-module guidance.
5. Invalid CUC test receives argparse exit `2` instead of the required `CUC validation failed: fingerprint mismatch`, proving validation cannot yet be reached.
6. Legacy `convert` still succeeds, but stderr is empty instead of the required deterministic deprecation diagnostic.

The existing standalone materialization tests remained green, so the compatibility path works before the change. This RED therefore proves #43 is missing orchestration/product surface rather than exposing a pre-existing failure in normalization, alignment, CUC indexing, module writing, PDF parsing, or Context-Fabric consumption.

GREEN must add only the frozen CLI/module orchestration and documentation behavior, preserving legacy `convert` materialization semantics apart from the explicit stderr deprecation message.
