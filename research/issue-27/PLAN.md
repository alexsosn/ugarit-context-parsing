# Plan: feature-only Burns Text-Fabric module (#27)

## Preconditions and scope

- Base branch contains merged #22 normalized Burns model, #23 reviewed CUC index/reference parser, and #26 deterministic alignment/report layer.
- Research is frozen in `research/issue-27/RESEARCH.md`.
- This slice writes/loads a Text-Fabric module only.
- #28 owns Context-Fabric composition; #29 owns product/Agora migration.
- No real Burns-derived fixture, module, report, or CI artifact may be committed/uploaded.

## Production seam

Add `src/ugarit_context_parsing/module.py` only after preserved RED.

Public API:

```python
@dataclass(frozen=True)
class BurnsModuleData:
    node_features: Mapping[str, Mapping[int, str]]
    metadata: Mapping[str, Mapping[str, str]]


def build_burns_module(
    source: NormalizedBurnsSource,
    alignments: tuple[BurnsAnnotationAlignment, ...],
    index: ReviewedCucIndex,
) -> BurnsModuleData: ...


def burns_node_annotations(value: str) -> tuple[dict[str, object], ...]: ...


def build_burns_module_report(
    source: NormalizedBurnsSource,
    alignments: tuple[BurnsAnnotationAlignment, ...],
    index: ReviewedCucIndex,
    module: BurnsModuleData,
) -> dict[str, object]: ...


def write_burns_module(
    module: BurnsModuleData,
    report: dict[str, object],
    output_dir: str | Path,
    *,
    fabric_factory: Callable[..., FabricLike] | None = None,
) -> bool: ...
```

Do not modify `graph.py` or the legacy standalone writer in this ticket.

## Exact feature inventory

The successful module stage may contain exactly:

- `burns_annotations.tf` — authoritative canonical JSON occurrence arrays;
- `burns_annotation_ids.tf` — projection;
- `burns_semantic_statuses.tf` — projection;
- `burns_worksheet_roles.tf` — projection;
- `burns_sections.tf` — projection;
- `burns_headwords.tf` — projection;
- `burns-module-report.json` — local report, not a TF feature.

Forbidden output includes at least:

- `otype.tf`, `oslots.tf`, `otext.tf`;
- copied CUC `g_cons.tf`, `tablet.tf`, `column.tf`, `line.tf`;
- any other unexpected `.tf` feature.

The exact allowed inventory makes accidental warp/config/feature leakage a hard error.

## Compatibility gate

`build_burns_module()` must require `index.compatibility` and require its repository/commit/version/manifest identity to equal the reviewed constants from `cuc_index.py`.

The module cannot be built against `compatibility=None`, a different CUC commit/version, or a mismatched manifest identity.

This check is separate from `build_reviewed_cuc_index()` so direct/synthetic callers cannot accidentally produce a production-looking module against an unbound index.

## Authoritative payload schema

Each selected alignment occurrence becomes one canonical payload:

```json
{
  "schema": "burns-node-annotation-v1",
  "annotation_id": "...",
  "occurrence_id": "...",
  "target_ordinal": 0,
  "record_ids": ["..."],
  "worksheet_id": "...",
  "workbook_number": 1,
  "workbook_label": "...",
  "worksheet_number": 1,
  "worksheet_role": "prime_gp",
  "section": "...",
  "root": "...",
  "headword": "...",
  "ktu": "...",
  "references": "...",
  "textual_status": "textual",
  "semantic_status": "positive_fixed",
  "interpretive_status": "unspecified",
  "disposition": "aligned",
  "reason": "none",
  "confidence": "exact_lexical",
  "anchor_kind": "word_span",
  "anchor_nodes": [320,321],
  "context_line_node": 203,
  "target": {"tablet":"KTU 1.14","column":"I","line":3},
  "candidate_line_nodes": [],
  "candidate_spans": []
}
```

The payload is built by joining #26 alignment to the matching #22 annotation ID. It must preserve annotation record IDs and taxonomy verbatim.

Before emitting payloads, call/reuse #26 report validation so forged/missing/extra alignment objects, source partition errors, and deterministic-resolution mismatches fail closed.

Only occurrences with a selected non-empty `anchor_nodes` tuple are emitted to node features. Unanchored outcomes remain in the report.

## Placement and deduplication

For each selected occurrence payload:

- tablet/line anchor: add to its one selected node;
- word-span anchor: add identical payload to every node in the complete ordered span.

Identity key:

`(annotation_id, occurrence_id, anchor_kind, tuple(anchor_nodes))`

Within one node:

- exact repeated identity + byte-identical payload -> keep one;
- repeated identity + differing payload -> fail closed;
- different identities remain distinct even if headword/category values are equal.

Sort authoritative entries by identity key. Serialize the per-node array with compact canonical JSON (`ensure_ascii=False`, `sort_keys=True`, compact separators).

## Projection features

For every node present in `burns_annotations`, derive directly from parsed authoritative payloads:

- `burns_annotation_ids`: sorted unique annotation IDs;
- `burns_semantic_statuses`: sorted unique semantic status strings;
- `burns_worksheet_roles`: sorted unique worksheet role strings;
- `burns_sections`: sorted unique section strings;
- `burns_headwords`: sorted unique headword strings.

Serialize each as a canonical JSON array. Do not derive projections independently from source/alignment data after the authoritative node payload has been built.

## Metadata

Every TF feature receives the same generic identity metadata plus feature-specific `description`:

- `valueType=str`;
- `module=Burns`;
- `moduleSchema=burns-tf-module-v1`;
- exact reviewed `cucRepository`, `cucCommit`, `cucVersion`, `cucManifestSha256`.

No `otext` config is emitted in v1.

## Module report

`build_burns_module_report()` first validates the supplied module against a fresh `build_burns_module()` result. A caller-modified feature/payload must not be reportable as authoritative.

Report schema `burns-tf-module-report-v1` contains:

- exact CUC compatibility object;
- source record/annotation counts;
- alignment disposition counts;
- selected occurrence count;
- anchor-kind counts;
- touched-node count;
- sorted exact feature inventory;
- embedded deterministic #26 alignment report under `alignment`.

The report is deterministic JSON-compatible data. Writer serializes it with sorted keys and a final newline.

## RED gate: synthetic core module tests

Create `tests/test_burns_tf_module.py` before `module.py` exists.

Synthetic normalized source/index/alignment fixtures must exercise:

1. import fails only because `ugarit_context_parsing.module` is absent;
2. a node with two distinct Burns annotations round-trips both payloads;
3. a two-word span is discoverable on both words but every copy contains the same complete ordered span and one occurrence ID;
4. nested/overlapping spans coexist without overwrite;
5. duplicate identical input occurrence serialization does not duplicate a node payload;
6. canonical output is independent of supplied alignment iteration order;
7. Unicode, newline, quote and punctuation in synthetic annotation fields survive `Fabric.save()` + reload + JSON parse;
8. projections exactly equal values derived from authoritative payloads;
9. exact CUC compatibility metadata appears on every feature;
10. a compatibility-less/mismatched index fails closed;
11. module/report builder rejects caller-modified alignment/module data;
12. no `otype.tf`, `oslots.tf`, `otext.tf`, or copied CUC feature is written;
13. writer rejects unexpected staged `.tf` inventory;
14. failed TF save leaves previous output intact;
15. mid-publication failure rolls back to previous complete module/report;
16. successful replacement removes stale Burns-owned TF files.

The preserved RED is valid only if the repository's prior tests remain green and new tests fail at the missing module import seam.

## GREEN implementation

Implement only `module.py` and the minimum tests/helpers necessary to satisfy the frozen core contract.

Use real Text-Fabric `Fabric.save()` in at least one synthetic test; injected fake Fabric is allowed only for deterministic failure/rollback tests.

Run the full Python 3.10/3.12/3.13 matrix plus existing Agora and Context-Fabric contracts.

## Post-core-GREEN real CUC integration

Extend `.github/workflows/test-reviewed-cuc-index.yml` without committing CUC files.

Against exact CUC commit `ad69400f...` and the public fingerprint gate:

1. build the real reviewed index;
2. dynamically choose an existing tablet, an exact line with words, and enough adjacent words to create legal synthetic annotations;
3. construct synthetic normalized Burns source/alignment through production APIs where possible; no Burns-derived strings;
4. write the module into a temp directory with real `Fabric.save()`;
5. load exact CUC base alone and capture:
   - `maxSlot`;
   - `maxNode`;
   - every node's `otype` (or exact type counts plus max bounds and representative navigation);
6. load CUC + Burns module from two locations;
7. require identical base warp/type values and unchanged structural navigation;
8. require Burns features to appear and parse through the combined Text-Fabric API;
9. require module directory exact inventory and no warp/copied CUC files.

This integration gate is separate from #28's Context-Fabric proof.

## Exact-head finalization

Freeze the final SHA. Require on that exact head:

- Tests workflow green on Python 3.10/3.12/3.13;
- installed-package checks green;
- Agora contract green;
- existing Context-Fabric contract green;
- reviewed-CUC module composition workflow green.

Then perform a logically independent adversarial review anchored to the exact final commit. Review must challenge all research risks and inspect the full PR diff, not merely confirm test names.

If review changes code/tests/docs, freeze the new head and repeat exact-head gates plus review.

Only then mark the PR ready and merge with `Closes #27` and expected-head protection.
