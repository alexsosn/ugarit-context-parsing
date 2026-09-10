# Plan: migrate the Burns product/Agora contract to a CUC feature module (#29)

Research: `research/issue-29/RESEARCH.md`.

Base at research start: `7d303a20314ab1350349f071dd597ff08f5629ef` (reviewed public `module` CLI merge).

## Dependency gate

Do not change the production manifest to `{parent}` until Agora #135 is merged and has an exact reviewed commit that accepts the parent placeholder/binding/sandbox/provenance contract. The existing CI intentionally pins an older Agora validator and asserts only the legacy materializer IDs, so the migration must update that consumer contract deliberately rather than silently relying on Agora `main`.

Provider-side automatic cached parent resolution (#146) and higher-level orchestration may land later; they are not required to truthfully declare the Burns producer as a CUC feature-module materializer. This ticket must not claim automatic parent acquisition until that separate path exists.

## Slice 1 — preserve manifest/product RED

Before changing `agora.materializer.json`, add focused repository tests requiring:

- materializer IDs, in stable order:
  1. `burns-workbooks-csv-cuc-module`;
  2. `burns-workbooks-pdf-cuc-module`;
  3. legacy `burns-workbooks-csv-text-fabric`;
  4. legacy `burns-workbooks-pdf-text-fabric`;
- each new module materializer:
  - keeps the same user-local source/glob/symlink policy as its corresponding legacy input;
  - executes `ugarit_context_parsing.cli module`;
  - passes `{source}`, exact `--input-format`, `--cuc {parent}`, and `{output}`;
  - keeps `network: deny`;
  - declares `output.format = text-fabric`;
  - declares `output.composition = {kind: feature-module, parent: cuc, compatibility.parent_versions: ["0.2.8"]}`;
  - requires exactly the six Burns node-feature files plus `burns-module-report.json`;
  - does not require `otype.tf`, `oslots.tf`, `otext.tf`, or copied CUC files;
- each legacy ID still executes `convert` with its historical CSV/PDF source mode and historical required output inventory;
- legacy descriptions are explicitly deprecated compatibility paths rather than the primary product;
- package/plugin version remains `0.2.0` in this ticket.

Expected RED: current manifest contains only the two legacy IDs.

Preserve exact failing CI before manifest changes.

## Slice 2 — manifest GREEN after Agora #135

After the exact #135 merge is known:

1. add the two new module entries to `agora.materializer.json` without repurposing the legacy IDs;
2. keep the existing legacy entries executable and mark their descriptions deprecated;
3. update the pinned Agora contract in `.github/workflows/test.yml` from the pre-parent validator to the exact reviewed #135 commit;
4. update the Agora-contract assertion to all four exact IDs and validate the new composition/parent placeholder through Agora's real `load_manifest()`;
5. do not change package/plugin version, release tracking, or software-license metadata.

Run full Python 3.10/3.12/3.13 plus Agora contract before the next slice.

## Slice 3 — preserve real host integration RED

Add a synthetic integration contract around the actual new CSV module manifest entry and reviewed CUC base. The test/workflow must:

- use only synthetic Burns CSV source rows;
- obtain the exact reviewed public CUC commit `ad69400f5446e1c8217af01659c7c10ab00c015b`, TF `0.2.8`;
- invoke the reviewed Agora host with an explicit trusted `ParentResourceBinding` for `cuc`, version `0.2.8`, that exact immutable revision and the CUC TF path;
- run the manifest's `burns-workbooks-csv-cuc-module`, not a hand-constructed duplicate command;
- keep network denied during converter execution;
- prove the artifact contains the six feature files + `burns-module-report.json` + Agora receipt and no warp files;
- prove the receipt preserves `output.composition` and observed parent resource/version/revision separately, without a parent host path;
- load the produced feature set together with CUC through the existing Context-Fabric/cfabric-mcp consumer contract and confirm base warp counts remain unchanged.

Before wiring this workflow/test, preserve a failing contract that demonstrates the current CI does not exercise the parent-aware manifest product path.

If #135's final registered-runner lifecycle requires a lease factory, this Burns repository should use the low-level reviewed host for this upstream contract unless the higher-level provider resolver/orchestrator is already merged. Do not fake a provider lease by claiming an arbitrary checkout is an Agora-managed cache object.

## Slice 4 — integration GREEN

Implement only the CI/workflow support required by Slice 3. Reuse existing reviewed-CUC and Context-Fabric helpers where possible instead of introducing a second CUC verifier or module loader.

The PDF module remains contract/schema tested here; its real parser/module behavior is already covered by the existing deterministic PDF and module CLI suites. Do not create or commit a copyrighted Burns PDF fixture.

## Slice 5 — documentation migration

Update README after the new manifest path is green:

- present the two CUC-module materializer IDs as the primary Agora product path;
- state that Agora supplies a separately trusted CUC parent; the Burns converter itself does not fetch it;
- state exactly what is currently automatic vs caller/orchestrator supplied based on merged Agora capabilities at that point;
- retain a compact explicit deprecation section for the two legacy standalone IDs and point removal to #39;
- remove stale wording claiming Agora cannot represent/pass a parent once #135 is merged;
- preserve CC BY-NC-ND source/derived-artifact redistribution warnings.

## Slice 6 — upstream exact-head review and merge

Freeze the exact Burns head and require:

- Python 3.10/3.12/3.13 suite;
- installed-package test;
- deterministic CSV/PDF tests;
- reviewed-CUC/module contract;
- Context-Fabric/cfabric-mcp contract;
- exact reviewed Agora #135 contract;
- no restricted Burns-derived files in the diff/artifacts.

Perform a logically independent adversarial review challenging:

- accidental reuse/semantic mutation of legacy IDs;
- new module entries accidentally using `convert`;
- warp/config files in module required/output inventory;
- wrong parent ID/version or mutable revision assumptions;
- implicit CUC fetch/network behavior by the converter;
- CI validating a hand-built command instead of the manifest entry;
- parent path leaked into durable provenance;
- package/plugin version or license claims changed without #15/#16;
- stale README claims about Agora parent support;
- downstream Context-Fabric test silently altering base warp;
- restricted source/derived data committed or uploaded.

Any finding becomes a focused RED before a fix. Re-freeze and re-review the corrected exact head.

## Slice 7 — downstream Agora registry update

Only after the Burns PR is merged and has a reviewed immutable commit:

- update Agora's `ugarit-context-parsing` registry pin to that exact commit;
- list the two CUC-module IDs as primary supported materializers while retaining the two legacy compatibility IDs;
- update registry verification notes to the real CUC feature-module architecture;
- keep `software: NOASSERTION` and release tracking disabled until #15/#16 resolve;
- run Agora registered-install/materializer validation against that immutable Burns commit;
- independently review and merge the Agora registry PR.

This downstream registry mutation is a separate repository PR even though it completes #29's cross-repository acceptance.

## Definition of done

A user can select a Burns CSV/PDF CUC-module materializer whose manifest truthfully declares CUC 0.2.8 as its parent, the converter runs its existing `module` CLI against a separately trusted parent path, the result is feature-only and composable with CUC, legacy standalone IDs still work but are explicitly deprecated, and Agora is pinned to the reviewed Burns commit without inventing a canonical repository resource for locally generated Burns data.
