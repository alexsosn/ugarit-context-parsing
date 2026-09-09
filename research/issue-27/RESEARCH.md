# Research: feature-only Burns Text-Fabric module (#27)

## Scope

This slice is the Text-Fabric writer/composition child of #21 and follows merged #26. It must not change the CUC warp, introduce Burns annotation nodes, migrate the current product/Agora path, or solve Context-Fabric composition (#28).

No restricted Burns-derived source/module artifact may be committed or uploaded. All committed fixtures must be synthetic.

## Existing Burns-side contracts

Merged #22 provides immutable normalized source records and semantic annotations with stable IDs and lossless provenance. Merged #23 provides the reviewed CUC fingerprint/index contract. Merged #26 provides deterministic alignment objects and a fail-closed alignment report:

- annotation-level dispositions distinguish aligned, ambiguous, partial, unresolved, out-of-CUC, and non-textual cases;
- each parsed target gets one ordered occurrence result;
- selected anchors are existing CUC tablet/line/word nodes only;
- a unique lexical match may be an ordered multi-word span;
- lexical/structural ambiguity is retained instead of first-hit guessed;
- the alignment report rejects forged alignment payloads and requires exact source-record partitioning.

Therefore #27 should consume #26 alignment output; it must not independently re-resolve scholarly references or headwords.

## Exact reviewed CUC compatibility

`cuc_index.py` binds production alignment to:

- repository: `DT-UCPH/cuc`;
- commit: `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- version: `0.2.8`;
- required-files manifest SHA-256: `717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba`;
- node counts: sign 146017, column 334, line 7616, tablet 279, word 27770.

The module writer must require a compatibility-bearing reviewed index and emit this identity into feature metadata and its report. A synthetic test index may use the same identity, but the permanent integration gate must build the index through `build_reviewed_cuc_index()` on the exact public CUC files.

## Text-Fabric 13.1.0 writer semantics

The installed runtime constraint is Text-Fabric `>=13.1,<14`. The exact reviewed upstream release is `annotation/text-fabric` tag `v13.1.0`, commit `dd227ce62b5536de53a0e20eac98c0459da8fd3d`.

At that commit:

1. `Fabric.save(nodeFeatures=..., edgeFeatures=..., metaData=..., location=..., module=...)` writes exactly the supplied node/edge/config features. `otype` and `oslots` are only warp features when explicitly supplied; they are not required to save ordinary node features.
2. Node-feature values are strings or integers. Burns multiplicity therefore needs one canonical string value per CUC node, not multiple TF feature rows for the same node.
3. `FabricCore` indexes all `.tf` files non-recursively under every `location/module` pair. Module order determines override precedence if names collide.
4. When a searched location lacks `otype`/`oslots`, TF treats it as feature-only. When the CUC base and Burns module locations are searched together, the base supplies the warp and Burns supplies only additional named features.
5. `loadAll()` loads the base warp plus all ordinary node/edge features visible in the combined feature inventory.

This gives a direct local composition contract:

```python
Fabric(locations=[str(cuc_tf_dir), str(burns_module_dir)], modules=[""], silent="deep")
```

No copy of CUC files is necessary or desirable.

## Authoritative representation

### `burns_annotations`

Use one authoritative **string node feature** named `burns_annotations`.

Its value is compact canonical JSON: an array of occurrence payload objects sorted by stable identity. One object corresponds to one selected #26 occurrence and contains enough information to reconstruct that occurrence independently of the node on which the value was discovered.

Minimum payload fields:

- schema/version;
- stable semantic `annotation_id`;
- stable `occurrence_id` and target ordinal;
- ordered source `record_ids`;
- annotation provenance/taxonomy needed by consumers: worksheet ID/number/role, workbook number/label, section, root, headword, KTU/reference, textual/semantic/interpretive status;
- occurrence disposition/reason/confidence;
- anchor kind;
- **complete ordered `anchor_nodes` tuple**;
- context line node;
- structured target;
- ambiguity candidate line/span tuples when present.

The canonical JSON itself is the authoritative source for Burns module annotations. Derived convenience features must be projections from these objects and may never contain information absent from the authoritative payload.

### Placement

- tablet occurrence: payload on the selected existing CUC tablet node;
- line occurrence: payload on the selected existing CUC line node;
- word-span occurrence: the identical full payload is discoverable on every participating existing CUC word node;
- unanchored ambiguous/unresolved/out-of-CUC/non-textual occurrences: no node feature entry; they remain fully accounted in the module/alignment report.

For a two-word span `(320, 321)`, nodes 320 and 321 both carry one payload whose `anchor_nodes` is `[320,321]`. A consumer groups/deduplicates by `(annotation_id, occurrence_id, anchor_kind, anchor_nodes)` and reconstructs one span, not two annotations.

### Multiplicity and overlaps

A CUC node may contain multiple payload objects. Nested/overlapping spans are legal. Canonical ordering and deduplication use stable occurrence identity plus the complete anchor tuple, never scholarly category/headword equality.

Exact duplicate input alignments should not produce duplicate entries on a node. Conflicting objects with the same occurrence identity but different anchor tuples must fail closed rather than silently choose one.

## Convenience projections

Provide conservative query-oriented string features derived only from the authoritative per-node payload list:

- `burns_annotation_ids` — canonical JSON array of unique annotation IDs;
- `burns_semantic_statuses` — canonical JSON array of unique semantic statuses;
- `burns_worksheet_roles` — canonical JSON array of unique worksheet roles;
- `burns_sections` — canonical JSON array of unique section strings;
- `burns_headwords` — canonical JSON array of unique source headwords.

These are intentionally multi-valued canonical JSON arrays rather than delimiter-concatenated strings, because Burns text may contain punctuation/newlines and no delimiter can be assumed absent. They are projections for discovery only; consumers needing provenance/span semantics parse `burns_annotations`.

Do not copy CUC diplomatic/linguistic features such as `otype`, `oslots`, `g_cons`, `tablet`, `column`, or `line`.

## Canonical serialization

Use `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"))`.

This preserves Unicode directly and escapes embedded newlines inside the single TF feature value. After TF save/reload, parsing the JSON recovers the original Unicode/newline/punctuation.

Per-node authoritative entries are sorted by `(annotation_id, occurrence_id, anchor_kind, anchor_nodes)` after exact deduplication. Projection arrays are sorted Unicode strings.

## Feature metadata

Every Burns node feature should carry matching module/base identity metadata, at minimum:

- `valueType=str`;
- `module=Burns`;
- `moduleSchema=burns-tf-module-v1`;
- `cucRepository=DT-UCPH/cuc`;
- `cucCommit=ad69400f5446e1c8217af01659c7c10ab00c015b`;
- `cucVersion=0.2.8`;
- `cucManifestSha256=717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba`.

No metadata field should imply that Burns owns the warp.

## Module report

Publish `burns-module-report.json` alongside the feature files. It should contain:

- schema `burns-tf-module-report-v1`;
- exact CUC compatibility identity;
- source record/annotation totals;
- alignment disposition counts;
- selected occurrence count;
- counts by anchor kind;
- touched CUC node count;
- feature inventory;
- embedded/reused deterministic alignment report so all unanchored source annotations remain accounted.

The full report is Burns-derived and is local output only; tests use synthetic source content.

## Transactional publication

The output directory is a dedicated Burns module directory. Build everything in a sibling temporary staging directory first:

1. call real `Fabric.save()` with only Burns node features and metadata;
2. assert the exact expected `.tf` inventory exists;
3. assert forbidden warp/CUC feature files do not exist;
4. write the module report in the stage;
5. replace the previous module-owned files/report as one rollback-capable publication step.

If TF save fails, validation fails, or installation raises midway, the previous published module/report must remain intact. Stale Burns feature files from an older schema must not survive a successful replacement.

## Combined-load proof

The permanent reviewed-CUC workflow should, on an ephemeral runner only:

1. check out exact CUC commit;
2. build the reviewed index through the public fingerprint gate;
3. create legal synthetic Burns annotations that exercise at least tablet, line, single-word, multi-word, and overlap/multiplicity behavior against existing CUC nodes discovered from the index;
4. write the Burns module to a temporary directory;
5. load CUC base alone and record `maxSlot`, `maxNode`, and complete `otype` counts;
6. load `[CUC base, Burns module]` with Text-Fabric;
7. assert identical `maxSlot`, `maxNode`, `otype` sequence/counts and base structural navigation;
8. assert Burns feature inventory/value round-trip through the combined API;
9. assert the Burns module directory contains no `otype.tf` or `oslots.tf` and no copied CUC features.

This is the real integration gate for #27. Context-Fabric composition remains #28.

## TDD seams

Preserve RED before `module.py` exists. Synthetic tests should define the intended public API and fail only because the writer/module seam is missing.

Planned API:

- `BurnsModuleData` immutable public result model;
- `build_burns_module(source, alignments, index)`;
- `burns_node_annotations(value)` parser/helper for authoritative feature values;
- `build_burns_module_report(source, alignments, index, module)`;
- `write_burns_module(module, report, output_dir, fabric_factory=None)`.

Core RED must cover issue #27's no-warp, multiplicity, multi-word reconstruction, overlap, deduplication, canonical order, Unicode/newline/punctuation, metadata, and transactional rules. Real combined CUC loading follows core GREEN in the permanent exact-CUC workflow.

## Risks / adversarial targets

Final independent review must specifically attack:

- accidentally creating annotation nodes or warp files;
- payload loss when multiple annotations share a node;
- treating a copied multi-word payload as multiple annotations;
- deduplicating by headword/category instead of stable identity;
- overwriting nested/overlapping spans;
- feature values containing non-canonical/order-dependent JSON;
- convenience projections diverging from `burns_annotations`;
- forged/mismatched alignment objects bypassing #26 validation;
- module metadata bound to the wrong CUC base;
- partial publication leaving mixed old/new files;
- combined loading overriding or changing CUC warp/features;
- restricted Burns-derived output appearing in repository/CI artifacts.
