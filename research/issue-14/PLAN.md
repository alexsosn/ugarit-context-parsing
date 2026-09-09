# Plan: pin Node-24 GitHub Actions releases (#14)

## Preconditions

- Research: `research/issue-14/RESEARCH.md`.
- Baseline: `master@c6f165a3ebf8c9ed3ef0bd2dc2a7bbc8090ed219`.
- Reviewed checkout target: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1).
- Reviewed setup-python target: `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` (v7.0.0).
- Issue #17 owns any change to head-vs-merge-ref CI provenance; this ticket changes action runtime references only.

## RED slice

Add `tests/test_ci_action_pins.py` before editing `.github/workflows/test.yml`.

The test will:

1. read only `.github/workflows/test.yml` from the repository checkout;
2. extract `uses:` values matching `actions/checkout@...` and `actions/setup-python@...`;
3. strip YAML comments from those values;
4. require exactly five checkout occurrences and three setup-python occurrences;
5. require every checkout occurrence to equal the reviewed v7.0.1 full SHA;
6. require every setup-python occurrence to equal the reviewed v7.0.0 full SHA.

No network calls, YAML dependency, or action execution are needed for this contract.

Expected RED on the unchanged workflow:

- five `actions/checkout@v4` references differ from the required checkout SHA;
- three `actions/setup-python@v5` references differ from the required setup-python SHA.

Open the PR while this RED is present and preserve CI evidence before implementation.

## GREEN slice

Change only the eight matching `uses:` lines in `.github/workflows/test.yml`:

- checkout refs → `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`;
- setup-python refs → `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`.

Do not edit trigger, permissions, matrices, cache inputs, repository pins, paths, commands, or contract assertions.

## GREEN gates

Require one CI run for the post-change PR state with:

- `test (3.10)` green;
- `test (3.12)` green;
- `test (3.13)` green;
- `agora-contract` green;
- `context-fabric-contract` green;
- the new workflow-reference contract passing inside each ordinary test job;
- environment-recording and installed-package steps still successful;
- job logs showing the pinned v7 actions and no checkout/setup-python Node-20 deprecation warning.

## Independent adversarial review

Freeze the final implementation head and review it as if authored independently. Challenge at least:

1. Are all five checkout uses upgraded, including both nested consumer checkouts?
2. Are all three setup-python uses upgraded?
3. Do full SHAs exactly resolve to the reviewed release commits rather than a short/mistyped prefix?
4. Could the test pass if an extra obsolete checkout/setup-python use were added?
5. Did the implementation change anything besides the intended action references and the offline test/research docs?
6. Are nested Agora/Context-Fabric exact `ref` pins and `path` values unchanged?
7. Is Python matrix/cache behavior unchanged?
8. Do logs actually eliminate the Node-20 warning rather than merely hiding it?
9. Does the final PR avoid conflating #14 with the CI provenance problem tracked by #17?

Any blocker requires a correction, fresh GREEN CI, and a new frozen-head review.

## Definition of done

Research → plan → RED → GREEN evidence is preserved; all eight action references use immutable reviewed Node-24 release SHAs; all existing CI behavior remains green; Node-20 deprecation warnings attributable to checkout/setup-python are gone; independent adversarial review finds no blocker before merge.
