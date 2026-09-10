# Research: migrate the Burns product/Agora contract to a CUC feature module (#29)

## Status

The architecture prerequisites are now real rather than aspirational:

- the public upstream CLI has a primary `module SOURCE --input-format {csv,pdf} --cuc CUC_TF_DIR --output OUTPUT` path;
- the module pipeline normalizes Burns records, verifies/indexes the exact reviewed CUC 0.2.8 base, aligns conservatively, and writes a feature-only Text-Fabric module plus `burns-module-report.json`;
- Context-Fabric/cfabric-mcp can load ordered CUC + Burns module locations without changing the CUC warp;
- Agora #134 is merged and lets a materializer output declare `kind: feature-module`, `parent: cuc`, and opaque compatible parent versions while preserving that declaration in trusted materialization provenance;
- Agora #135 is the remaining generic execution prerequisite for supplying a separately prepared, immutable CUC parent path to `{parent}` under the materializer sandbox.

## Current product mismatch

`agora.materializer.json` still exposes only the two original standalone row-slot materializers:

- `burns-workbooks-csv-text-fabric`;
- `burns-workbooks-pdf-text-fabric`.

Both still execute deprecated `convert` and require `otype.tf`, `oslots.tf`, `otext.tf`, and `conversion-report.json`. The manifest therefore contradicts the reviewed product architecture even though the library/CLI can already produce the correct CUC module.

The README's CLI section has been migrated, but the Agora contract cannot be called complete while the published manifest/registry still selects the standalone topology.

## Compatibility decision: do not silently repurpose existing IDs

Changing either existing materializer ID in place from standalone corpus output to parent-dependent feature-module output would be a hidden breaking change:

- callers installed by immutable ID would suddenly require a second input;
- required output inventory and TF topology would change;
- receipts/cache identities tied to the same materializer ID would describe materially different products;
- the repository cannot responsibly hide that change behind the still-advertised `0.2.0` while software-license/release work remains blocked by #15/#16.

Therefore #29 should add new primary IDs and retain the old IDs unchanged as deprecated compatibility paths until the dedicated removal decision in #39.

Proposed primary IDs:

- `burns-workbooks-csv-cuc-module`;
- `burns-workbooks-pdf-cuc-module`.

The legacy IDs remain executable via `convert` and keep their original output requirements. Their descriptions/docs must explicitly call them deprecated compatibility materializers.

## New manifest contract

Each CUC-module materializer should:

1. retain the same user-local source acquisition and symlink policy as its legacy CSV/PDF counterpart;
2. execute the existing upstream CLI, not duplicate pipeline code:
   - `module {source} --input-format csv --cuc {parent} --output {output}`; or
   - `module {source} --input-format pdf --cuc {parent} --output {output}`;
3. keep `network: deny`;
4. declare feature-only required output paths:
   - `burns_annotations.tf`;
   - `burns_annotation_ids.tf`;
   - `burns_semantic_statuses.tf`;
   - `burns_worksheet_roles.tf`;
   - `burns_sections.tf`;
   - `burns_headwords.tf`;
   - `burns-module-report.json`;
5. declare exactly one output composition:
   - `kind: feature-module`;
   - `parent: cuc`;
   - `compatibility.parent_versions: ["0.2.8"]`.

The new outputs must not require or generate `otype.tf`, `oslots.tf`, or `otext.tf`.

## Parent identity and acquisition boundary

The manifest declares *which* parent is required. It must not fetch CUC itself or infer CUC from the Burns source tree.

After Agora #135, trusted higher-level orchestration supplies an immutable `ParentResourceBinding` for canonical `cuc` 0.2.8 and the low-level host mounts that prepared TF directory separately read-only. The converter remains network-denied.

Automatic canonical-parent preparation, managed artifact caching and path-free Context-Fabric hand-off are broader managed-composition work (#99/#100/#101). #29 must not claim those unfinished capabilities. It only has to make the producer and Agora registry truthfully represent Burns as a CUC module rather than a fake standalone corpus.

## Version/release boundary

Do not guess a software license and do not cut or imply a stable release in #29.

- package/plugin version remains `0.2.0` unless #15/#16 are separately resolved through their own research/TDD gates;
- Agora `software: NOASSERTION` remains truthful;
- release tracking remains disabled;
- downstream Agora registration may pin the reviewed #29 commit directly, as it already uses immutable commit pins.

New materializer IDs make the changed product semantics explicit without reusing the legacy IDs under the same version string.

## Downstream Agora registry migration

After the upstream manifest head is frozen and reviewed, Agora should update the registered `ugarit-context-parsing` commit to that exact immutable upstream head and list the two new CUC-module IDs as the primary supported product while retaining the two legacy IDs as compatibility entries until #39.

Verification notes must change from “CUC compatibility is limited to identifier/language conventions” to the actual reviewed model: Burns is a feature-only module over exact CUC 0.2.8 and the parent is a separate trusted input.

No Burns materialized output should be inserted into canonical `resources.yaml` as a fake repository-backed feature module. Its feature-module relationship lives in the materializer output composition/receipt.

## Evidence strategy

Synthetic data is sufficient for CI and avoids redistributing Burns-derived material.

The migration needs tests that prove:

- new module IDs exist with exact parent composition and `{parent}` execution;
- new required output inventory is feature-only and excludes warp/config files;
- legacy IDs still invoke `convert` and retain their old required output inventory;
- the manifest validates against the merged Agora parent-input contract;
- at least the CSV module path can execute through Agora's real host using synthetic Burns CSV plus an exact reviewed public CUC checkout/binding, producing only the Burns module files and a trusted parent identity receipt;
- existing public CLI + Context-Fabric composed-load contract remains green.

The PDF module can be contract-checked here because the upstream repository already has real-parser PDF determinism and module-CLI coverage; no copyrighted fixture is needed.

## Failure/rollback boundary

Do not remove the working legacy materializers in this ticket. If the new parent-aware path is unavailable or an older Agora host is used, users retain an explicitly deprecated compatibility path rather than receiving a silent topology change.

## Out of scope

- deleting legacy `convert` or legacy materializer IDs (#39);
- inventing/choosing the software license (#15);
- cutting a stable release or enabling release tracking (#16);
- automatic parent resolution/dependency solving;
- managed artifact cache/load/orchestration (#99/#100/#101);
- copying CUC warp/data into Burns output.
