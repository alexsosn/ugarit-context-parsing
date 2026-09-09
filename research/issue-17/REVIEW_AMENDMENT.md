# Review amendment: provenance coverage and base movement (#17)

A pre-final adversarial pass after the first GREEN implementation found two issues in the evidence contract and research wording.

## Finding 1: global invocation count was insufficient

The initial offline workflow contract required exactly three provenance invocations globally. That could pass if all three invocations were accidentally placed in one job while another independently checked-out job had none.

### Amendment

Require the `test`, `agora-contract`, and `context-fabric-contract` job blocks to each contain exactly one `python scripts/check_ci_provenance.py` invocation, while retaining the global total guard. Add a parser self-test proving steps remain associated with their own top-level jobs.

## Finding 2: base-branch movement was overstated

The initial research text said a base-branch movement would regenerate the pull-request merge ref and schedule fresh `pull_request` CI. GitHub's documented default `pull_request` trigger runs for `opened`, `synchronize`, and `reopened`; `synchronize` describes head-branch updates. The documentation does not justify assuming every base-only movement produces a fresh workflow run.

### Corrected finalization model

- Provenance attestation proves the exact base/head pair present in the synthetic merge that a particular CI run tested.
- `expected_head_sha` atomically prevents merging a different PR head than the frozen reviewed head.
- Before merge, the process must also compare the PR's current base SHA with the attested CI base SHA and refuse to describe stale CI as current-base evidence.
- There is no `expected_base_sha` parameter in the merge operation used by this loop, so repository-level required-check / up-to-date enforcement remains necessary to close the residual base-movement race. Issue #19 owns that control.

The #17 implementation therefore improves evidence accuracy without claiming repository-admin enforcement it does not provide.
