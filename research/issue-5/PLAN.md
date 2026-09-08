# Plan: semantic replay comparator and environment evidence (#5)

## Goal

Turn the merged CSV repeated-run proof into one explicit, negative-tested semantic comparison contract and record the exact CI execution environment used as evidence, without changing converter output semantics.

PDF real-parser determinism is explicitly split to #6.

## Preconditions

- Research: `research/issue-5/RESEARCH.md`.
- Baseline: `master@f271e5697a2dc5c13c783338e2a603ab5434678b`.
- Existing CSV evidence test remains the legal synthetic fixture and real materialization path.
- The only allowed TF volatility exclusion is an exact `@dateWritten=` line, required once per generated `.tf` file.

## RED slice

Update `tests/test_text_fabric_integration.py` before creating any comparator helper.

The test must:

1. build two distinct absolute CSV source roots with identical relative paths/bytes and opposite creation order;
2. materialize both through the real CLI/Text-Fabric writer;
3. preserve the existing source-immutability and expected-structure assertions;
4. import the planned private comparator only inside the evidence test;
5. require the untouched pair to compare equal;
6. copy one completed output to a third directory before either side of that negative pair is loaded;
7. make one valid scholarly mutation in the copied `cuc_tablet.tf` (replace the synthetic `KTU 1.14` value with another canonical-looking value);
8. require the comparator to report the TF/node-feature mismatch for the perturbed copy.

At this commit `_semantic_compare.py` must not exist. The exact-head PR CI should fail specifically because the planned comparator module is missing. Preserve the failed run as RED evidence.

## GREEN comparator

Add `src/ugarit_context_parsing/_semantic_compare.py` with a private test/evidence API:

```python
compare_text_fabric_artifacts(left, right) -> tuple[str, ...]
```

An empty tuple means semantic equality under the reviewed execution identity. Non-empty entries are stable difference categories sufficient for diagnosing which contract surface diverged.

The comparator must independently inspect both artifact directories and cover:

### Persisted artifact surface

- required files: `otype.tf`, `oslots.tf`, `otext.tf`, `conversion-report.json`;
- exact generated top-level `.tf` filename set;
- exactly one `@dateWritten=` line per generated `.tf` file;
- exact remaining text of every `.tf` file after removing only that line;
- complete parsed `conversion-report.json` equality, with parse/missing failures reported.

### Loaded Text-Fabric surface

Load both directories independently with `Fabric(...).loadAll()` and compare:

- `maxSlot` and `maxNode`;
- complete node-type sequence;
- sorted node-feature inventory;
- every node-feature value on every node;
- sorted edge-feature inventory;
- every forward edge target/value on every node, normalizing unvalued tuples and valued mappings into deterministic comparable forms;
- `T.sectionFromNode()` for every non-slot node when node bounds permit comparison.

The helper must not ignore path-like fields, report fields, metadata, whitespace, feature ordering, or unknown future TF files. A new persisted field therefore fails closed.

If either artifact cannot load, report that as inequality rather than silently comparing only the surviving side.

## Negative-control semantics

The positive pair must return `()`.

The perturbed copy must return a non-empty tuple containing at least:

- a normalized persisted-file difference for `cuc_tablet.tf`; and
- a loaded node-feature difference for `cuc_tablet`.

This prevents a comparator that merely checks filenames/counts/report status from passing the evidence test.

## CI environment evidence

Extend `.github/workflows/test.yml` after installation and before the test suite with `Record execution environment`.

For each Python matrix job, print one canonical JSON object containing:

- `python_version` (`sys.version`);
- `python_implementation`;
- `platform`, `system`, `release`, and `machine`;
- sorted installed distributions as `name==version`.

Also print `execution_environment_sha256=<digest>` where the digest is SHA-256 of that canonical JSON representation.

Use only Python standard-library facilities (`platform`, `sys`, `importlib.metadata`, `json`, `hashlib`) so the evidence step cannot fail because an additional reporting dependency is absent.

The log is evidence for that exact CI job only; it is not a lockfile and does not authorize a different Agora dependency closure.

## GREEN gates

After adding the comparator and workflow evidence:

- require the full repository test suite on Python 3.10, 3.12, and 3.13;
- require installed-package verification on all matrix cells;
- require the pinned Agora manifest-contract job;
- inspect each test job log/output to confirm the environment evidence step ran successfully;
- ensure the negative-control regression passes for the expected reasons.

## Independent adversarial review

Freeze the final head and review without relying on implementation rationale. Challenge at least:

- whether any generated TF file can escape comparison;
- whether `@dateWritten` is the only exclusion and is enforced exactly once;
- whether the comparator can return equality when a required file/report is missing or malformed;
- whether all node feature values are compared, including absent/empty values;
- whether every edge target/value is compared for valued and unvalued edge features;
- whether the negative mutation is syntactically loadable and reaches the loaded-feature check rather than only a textual mismatch;
- whether Text-Fabric caching could invalidate the negative test;
- whether environment evidence is emitted after dependency resolution and before replay;
- whether any wording accidentally claims PDF determinism or cross-environment identity.

Any blocker starts a regression sub-loop and requires fresh exact-head CI/review.

## Definition of done

- research -> plan -> failing comparator-contract commit -> helper/workflow GREEN history is preserved;
- CSV real materializer still runs twice on legal synthetic sources;
- one explicit comparator covers persisted TF, complete report, all loaded nodes/features, all loaded edges, and navigation;
- a scholarly negative mutation is rejected by both persisted and loaded semantic checks;
- each successful matrix job publishes exact environment/dependency identity plus digest;
- PDF remains explicitly unproven and tracked in #6;
- frozen exact head passes logically independent adversarial review before merge.
