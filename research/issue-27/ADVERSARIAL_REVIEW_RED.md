# Adversarial review RED: Burns TF module (#27)

Reviewed GREEN head: `3b9e089d06e3994344cebe04845f6d5650b0ebe9`.

The reviewed-CUC composition gate and full test matrix are green on that head, but a logically independent API-integrity pass found two blockers before finalization.

## Finding 1 — annotation-level partiality is lost on selected nodes

`BurnsAnnotationAlignment` distinguishes the annotation-level disposition/reason from each child occurrence. A mixed reference such as one resolved line plus one missing line is `partial / mixed_target_results` at annotation level while the selected occurrence itself remains `aligned`.

The current node payload serializes only the child occurrence's `disposition`/`reason`. A consumer discovering the selected node can therefore mistake a partially resolved Burns annotation for a wholly aligned annotation unless it separately joins the local module report.

Required fix: retain existing occurrence-level `disposition`/`reason` semantics and add explicit authoritative `annotation_disposition` and `annotation_reason` fields to every selected occurrence payload.

## Finding 2 — writer trusts caller-supplied projections and compatibility metadata

`build_burns_module_report()` rejects a caller-modified module when source/alignment/index are available, but the public `write_burns_module(module, report, ...)` API accepts a manually constructed `BurnsModuleData`. `_validate_module_for_write()` currently verifies feature inventory, node coverage, authoritative JSON shape, and only two metadata fields. It does not re-derive convenience projections from `burns_annotations` or require the complete reviewed CUC metadata/report identity.

Required fix: before constructing Text-Fabric or touching publication state, the writer must:

- parse authoritative values and re-derive every projection exactly;
- reject any projection byte/value divergence;
- require exact v1 metadata for every feature, including `module=Burns`, reviewed CUC repository/commit/version/manifest, and the feature-specific description;
- require the report's CUC compatibility object to equal the same reviewed identity.

## Preserved adversarial RED

Add a separate synthetic test module before changing production code. It must prove:

1. a real mixed-target alignment is annotation-level `partial` while its selected occurrence remains occurrence-level `aligned`, and require both levels in the node payload;
2. a forged projection is rejected by `write_burns_module()` before Fabric construction;
3. forged CUC feature metadata is rejected before Fabric construction;
4. forged report CUC compatibility is rejected before Fabric construction.

No Burns-derived fixture or output may be committed or uploaded. After the RED is observed, make the narrow production fix, rerun the full matrix and reviewed-CUC composition gate, then restart exact-head adversarial review.