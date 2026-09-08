# Plan: harden Burns CSV determinism evidence (#5)

## Goal

Close the remaining evidence gaps in the already-merged Burns CSV repeated-run test so Agora can independently review/replay a complete semantic determinism contract for one exact verified runtime environment.

The merged #4 replay remains the foundation. #5 must strengthen it without weakening its exhaustive normalized `.tf` comparison or changing converter production behavior unless a real semantic delta is exposed.

## Preconditions

- Research: `research/issue-5/RESEARCH.md`.
- Current baseline: `master@f271e5697a2dc5c13c783338e2a603ab5434678b`.
- Existing repeated-run test in `tests/test_text_fabric_integration.py` is preserved.
- No Burns-derived source/generated artifact may be committed or uploaded.
- CSV and PDF determinism remain separate claims; this slice is CSV only.

## Existing evidence that must remain green

The current test already requires:

- two real CLI conversions into distinct fresh output roots;
- identical synthetic source bytes across distinct source roots and opposite creation order;
- exact equality of every generated `.tf` file after removing only `@dateWritten=`;
- exact conversion-report equality;
- independent `Fabric(...).loadAll()` of both outputs;
- dynamic equality of `Fall()` and `Eall()` inventories;
- complete node-feature equality across the full node range;
- node type and section/navigation equality.

Do not replace these with a weaker helper-only assertion.

## Missing semantic-snapshot contract

Add a test-only `_semantic_snapshot(output)` seam over the already-loaded real Text-Fabric output. Its normalized result must include:

1. all node features named by `Fall()` and every `(node, value)` mapping;
2. all edge features named by `Eall()` and every `(source, targets/values)` mapping from `Es(feature).items()`;
3. feature metadata for every node/edge feature, excluding only Text-Fabric-generated `dateWritten`;
4. `maxSlot`, `maxNode`, and complete structural section/navigation tuples;
5. the complete parsed `conversion-report.json` object.

Canonicalization rules:

- preserve integer node/target identity;
- sort set/frozenset edge targets deterministically;
- preserve valued-edge target→value mappings;
- recursively canonicalize dict/list/tuple/set containers without converting distinct scalar values into one representation;
- never ignore an unknown feature merely because the test did not anticipate its name.

## Fixture hardening

Extend the existing synthetic determinism fixture only enough to force duplicate hierarchy occurrence labels. Within one worksheet, create a non-contiguous repeated section and/or repeated entry label so `_occurrence_label()` must emit `~2`.

Assert the expected suffixed section/entry label after real reload. Keep source creation-order inversion and all existing Unicode/KTU/source-provenance coverage.

## RED — missing semantic evidence seam

Commit tests before implementing `_semantic_snapshot`.

The RED commit must modify test code only and must:

1. preserve and execute all existing repeated-run assertions first;
2. emit a canonical `DETERMINISM_ENVIRONMENT=<json>` line from the current test process;
3. call `_semantic_snapshot(output_a)` and `_semantic_snapshot(output_b)` after both real conversions/reloads have succeeded;
4. compare snapshots for equality;
5. contain a deliberate `_semantic_snapshot` implementation that raises `NotImplementedError("semantic snapshot not implemented")` so the exact commit is observably RED for the intended missing test-harness contract;
6. include the planned negative-control assertions in the test body, even though execution stops at the deliberate seam in RED.

Expected RED: all prior materialization/reload checks succeed, then the test errors specifically at the unimplemented semantic snapshot seam. No converter source file changes.

## GREEN 1 — implement semantic snapshot in tests only

Replace the deliberate `NotImplementedError` with the minimal test-only normalizer.

Do not change converter production code if the real outputs are semantically equal.

If the snapshots differ:

1. preserve the failing exact head;
2. inspect the first semantic difference;
3. determine whether it is legitimate generated volatility already excluded by the one-field `dateWritten` rule;
4. if not, add a focused converter regression RED before any production fix;
5. do not broaden metadata/feature ignores merely to force GREEN.

## GREEN 2 — negative controls

Prove the snapshot/equality path is non-vacuous by deep-copying a real normalized snapshot and independently changing:

- one node-feature value;
- one edge target/value from `oslots` or another emitted edge feature;
- one `conversion-report.json` value.

Each altered copy must compare unequal to the original. These mutations are test-memory only and do not modify converter outputs.

## Environment evidence

Add one helper that prints canonical JSON prefixed exactly with `DETERMINISM_ENVIRONMENT=`. Include at least:

- Python implementation and full version;
- `sys.platform` / operating system / release / machine;
- sorted installed distributions as `(normalized-name, version)` pairs.

Use installed-distribution metadata from the current process. The log record is upstream evidence only; Agora still binds authorization to its own integrity-verified `execution_identity_sha256` and must replay in that exact managed environment.

Do not upload generated TF directories or source fixtures as Actions artifacts.

## Test gates

Final exact head must pass the repository's unchanged ordinary workflow:

- Python 3.10 full suite;
- Python 3.12 full suite;
- Python 3.13 full suite;
- installed-package-outside-checkout verification;
- Agora manifest-contract validation.

The determinism test must emit one environment record in each Python matrix cell.

## Independent adversarial review focus

Freeze the final exact head and review the actual patch without relying on this plan. Challenge at least:

1. whether every `Fall()` mapping is preserved;
2. whether every `Eall()` mapping/value is preserved, not just feature names;
3. whether metadata comparison excludes anything besides generated `dateWritten`;
4. whether the raw normalized `.tf` backstop is still present;
5. whether negative controls can actually falsify equality;
6. whether duplicate occurrence-label state is exercised rather than merely assumed deterministic;
7. whether both outputs are still produced by the real CLI and independently reloaded;
8. whether environment evidence reports the resolved process rather than a declared dependency range;
9. whether any CSV conclusion is improperly generalized to PDF;
10. whether restricted Burns data or generated artifacts entered the diff/log/artifacts.

Every blocker becomes a focused RED regression before its fix.

## Definition of done

#5 is complete for CSV when the frozen PR head preserves the merged #4 replay, adds complete loaded edge/metadata semantic equality plus negative controls and duplicate-label coverage, emits reproducible environment evidence across the supported Python matrix, passes all ordinary CI gates, and receives a fresh logically independent adversarial review with no blocker.

PDF remains un-attested until a separate real-parser synthetic-PDF evidence loop is completed.
