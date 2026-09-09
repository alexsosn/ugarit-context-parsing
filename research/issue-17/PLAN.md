# Plan: attest pull-request merge provenance (#17)

## Preconditions

- Research: `research/issue-17/RESEARCH.md`.
- Baseline: `master@3c323f6540c9b8d791be3f62b1a6fbdd505243b5`.
- Keep existing `pull_request` merge-ref checkout semantics.
- Issue #19 separately owns repository-level required-check enforcement.

## RED slice

Add `tests/test_ci_provenance_contract.py` before adding any provenance script or workflow step.

The test will scan every workflow YAML file and require exactly three command occurrences of:

`python scripts/check_ci_provenance.py`

One occurrence belongs to the matrix `test` job definition, one to `agora-contract`, and one to `context-fabric-contract`. The baseline has zero, so the first CI run must fail only this new contract while existing behavior remains otherwise unchanged.

Open a draft PR on that RED head and preserve the failing run before implementation.

## GREEN implementation

### Provenance script

Add `scripts/check_ci_provenance.py` with a pure validation function and a thin environment/Git wrapper.

Pull-request mode inputs:

- event payload `pull_request.head.sha`;
- event payload `pull_request.base.sha`;
- `GITHUB_SHA`;
- checked-out `git rev-parse HEAD`;
- `git rev-list --parents -n 1 HEAD`.

Require:

- `HEAD == GITHUB_SHA`;
- exactly two merge parents;
- parent 1 equals event base SHA;
- parent 2 equals event head SHA.

Emit canonical JSON prefixed by `ci_provenance=` containing:

- `mode: pull_request_merge`;
- `tested_sha`;
- `head_sha`;
- `base_sha`;
- ordered `parents`.

Push mode requires `HEAD == GITHUB_SHA` and emits `mode: push`, `tested_sha`, and empty/no PR-parent claims.

Fail closed for unsupported/malformed pull-request event data.

### Unit tests

Extend the RED test file to cover the pure validator:

1. valid PR merge;
2. checked-out SHA differs from `GITHUB_SHA`;
3. parent count is not two;
4. base/head parent order mismatch;
5. missing pull-request payload fields;
6. valid push;
7. push checkout mismatch.

### Workflow integration

Add a step named `Verify CI provenance` immediately after setup-python in each top-level job definition:

`run: python scripts/check_ci_provenance.py`

Do not alter checkout refs, triggers, permissions, matrices, cache settings, consumer pins, or test commands.

## GREEN gates

Require one current pull-request run with:

- `test (3.10)` green;
- `test (3.12)` green;
- `test (3.13)` green;
- `agora-contract` green;
- `context-fabric-contract` green;
- each job's provenance step green;
- logs showing `ci_provenance=` with the same event head/base and tested merge SHA for every job in the run;
- existing action-pin, environment, installed-package, Agora, and Context-Fabric contracts still green.

Also inspect the subsequent push-to-master run after merge if available; push-mode support is primarily covered offline and must not block PR finalization.

## Independent adversarial review

Freeze the final head and challenge:

1. Does every independently checked-out job run provenance validation?
2. Could a matrix/contract job bypass the assertion?
3. Does the validator compare actual Git `HEAD`, not merely environment variables against themselves?
4. Are both event base/head SHAs tied to ordered merge parents?
5. Does malformed event data fail closed?
6. Is push behavior distinct from PR merge behavior?
7. Did any implementation accidentally switch PR jobs to head-only checkout?
8. Are action pins and downstream repository pins unchanged?
9. Are logs machine-readable and sufficient to distinguish frozen head from tested merge result?
10. Is merge finalization protected by `expected_head_sha` equal to the reviewed frozen head?
11. Is repository-protection enforcement correctly left to #19 rather than overstated here?

Any blocker requires correction, fresh CI, and a new frozen-head review.

## Definition of done

Research → plan → preserved RED → GREEN history exists; every required job attests its actual merge-result checkout; terminology distinguishes frozen head from tested merge; all functional/downstream gates remain green; independent review finds no blocker; merge uses `expected_head_sha`.
