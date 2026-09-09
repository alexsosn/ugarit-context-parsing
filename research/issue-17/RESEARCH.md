# Research: frozen-head and merge-result CI provenance (#17)

## Question

How should this repository prove which revision GitHub Actions actually tested for a pull request while preserving merge-result coverage and preventing finalization of a different head than the reviewed one?

## Baseline

Repository baseline: `master@3c323f6540c9b8d791be3f62b1a6fbdd505243b5`.

The workflow runs on `pull_request` and uses default checkout semantics. Live evidence from PR #18 shows GitHub fetched `refs/pull/18/merge` and checked out a synthetic merge commit whose parents were the base and PR head. The workflow-run API separately associated the run with the literal PR head SHA.

Calling this evidence “exact-head CI” is inaccurate: the jobs test the merge result, not a checkout of the head commit by itself.

## Evidence model

Keep merge-result testing. It is valuable because it tests the proposed change integrated with the base branch. Do not replace it with head-only checkout.

For every required job, add an explicit provenance assertion after checkout and Python setup. On `pull_request` it must:

1. read `GITHUB_EVENT_PATH`;
2. obtain `pull_request.head.sha` and `pull_request.base.sha` from the event payload;
3. obtain the checked-out `HEAD` and its parent SHAs from Git;
4. require checked-out `HEAD == GITHUB_SHA`;
5. require exactly two parents for the synthetic merge commit;
6. require the PR head SHA to be the second parent and the base SHA to be the first parent;
7. emit one canonical machine-readable provenance line containing mode, tested merge SHA, head SHA, base SHA and parents.

For `push` runs on `master`, require only `HEAD == GITHUB_SHA` and emit `mode=push`; no synthetic-merge claim applies.

The parent-order assertion is intentional. GitHub's pull-request merge ref is constructed as base parent first and PR head parent second, and live repository evidence demonstrates that contract. If GitHub changes that semantics, CI should fail visibly rather than silently weakening provenance meaning.

## Placement

Each top-level job checks out the repository independently. A single standalone provenance job would prove its own checkout but not literally prove the checkout used by the Python matrix, Agora contract, or Context-Fabric contract. Therefore each job definition should invoke the same provenance script after checkout/setup:

- `test` matrix definition: one workflow invocation, executed separately in each matrix cell;
- `agora-contract`: one invocation;
- `context-fabric-contract`: one invocation.

Total workflow invocations: three, producing five runtime attestations per pull-request run because the Python job expands to three matrix cells.

## Finalization semantics

A successful attested PR run proves that the tested synthetic merge contained the event's exact PR head and base commits. Finalization must still use GitHub's merge API with `expected_head_sha=<reviewed head>`.

These controls cover different races:

- provenance attestation proves what the successful CI run tested;
- `expected_head_sha` rejects a merge if the PR head moved after review/CI;
- a base movement causes GitHub to regenerate the pull-request merge ref and schedule fresh `pull_request` CI, so old merge-result evidence must not be described as current base-integration evidence.

Repository-level enforcement of required checks is separate. `master` is currently unprotected and has no rulesets; issue #19 tracks that administrative control.

## Terminology

Use:

- **frozen reviewed head** for the literal PR head SHA reviewed by the agent;
- **attested merge-result CI** for a successful pull-request run whose checked-out synthetic merge was verified to contain the exact event head/base commits;
- **head-only CI** only if a job actually checks out `pull_request.head.sha` directly.

Do not call merge-ref-only CI “exact-head CI”.

## TDD gate

Before adding the provenance implementation or workflow invocations, add a focused offline test requiring:

- `scripts/check_ci_provenance.py` to exist as the supported contract entry point only after GREEN;
- exactly three workflow command invocations of `python scripts/check_ci_provenance.py` across all workflow YAML files.

The first RED should be preserved while the workflow has zero invocations. Then implement the script and invoke it in all three job definitions.

The implementation script should expose a small pure validation function so unit tests can cover pull-request success, wrong checked-out SHA, wrong/missing parents, and push-mode behavior without depending on GitHub or a live Git repository.

## Acceptance evidence

After GREEN:

- Python 3.10/3.12/3.13 jobs each attest their actual checkout and remain green;
- Agora and Context-Fabric jobs attest their actual checkout and remain green;
- pull-request logs include canonical provenance evidence containing tested merge/head/base SHAs;
- ordinary push-to-master runs remain supported;
- workflow action-pin guards remain green;
- no job is switched from merge-ref to head-only testing;
- final PR is merged only with `expected_head_sha` matching the reviewed frozen head.
