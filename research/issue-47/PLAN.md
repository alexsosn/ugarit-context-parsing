# Plan: correct deferred Agora parent-resource status (#47)

Research: `research/issue-47/RESEARCH.md`.

This is a documentation-correctness slice. It must not change converter behavior, `agora.materializer.json`, package/plugin version, release metadata, licensing, or scholarly output.

## RED — status documentation contract

Add a focused test that extracts README's `### Agora status` section and requires:

- current registration is described as legacy one-source/single-input materializers;
- the reviewed CUC-aligned module remains described as available through the public `module` CLI;
- parent-aware Agora module execution/registration is explicitly described as deferred or unavailable in current supported Agora scope;
- `alexsosn/Agora#135` is identified as the closed/deferred prerequisite;
- Burns `#29` is identified as the migration tracker;
- the existing refusal to fake composition by copying CUC or enabling implicit network fallback remains documented;
- stale phrase `Until that lands` is forbidden.

Expected RED: current README still describes #135 as pending and contains `Until that lands`.

## GREEN — minimal README correction

Rewrite only the `### Agora status` section:

1. preserve the two current legacy materializer IDs;
2. explicitly separate completed local CUC-module functionality from blocked Agora representation;
3. state that Agora #135 was closed `not planned` / parent-resource execution was deferred from current supported scope;
4. point to Burns #29 as the migration tracker and preserved RED;
5. state that migration resumes only if Agora restores a truthful parent-resource contract;
6. retain the no-copy/no-network/no-fake-one-input boundary.

Do not modify manifest or CLI examples in this ticket.

## Verification

Run full Python 3.10/3.12/3.13 tests, installed-package smoke, Agora contract, Context-Fabric consumer contract, and any dedicated reviewed-CUC/module workflows automatically triggered by the branch.

## Independent adversarial review

Freeze one exact head and challenge:

- accidental claim that the Burns module itself is blocked/incomplete;
- accidental claim that current Agora can execute the parent-aware module;
- implying #135 was implemented rather than deferred;
- deleting useful migration references/history;
- suggesting copied CUC data, network fallback, or a fake standalone feature module as workaround;
- unrelated manifest/version/license/code changes;
- brittle test dependence on irrelevant prose/formatting.

Merge only after exact-head CI is green and commit-anchored logically independent review has no blocker.
