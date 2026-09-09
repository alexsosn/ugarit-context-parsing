# Plan: Context-Fabric CUC + Burns module composition (#28)

Frozen after `RESEARCH.md`; implementation must not silently widen this scope.

## Contract

Prove one logical cfabric-mcp corpus can be assembled from two ordered locations:

- location 1: exact reviewed public CUC 0.2.8 base;
- location 2: separately written feature-only Burns module generated from synthetic Burns rows.

No CUC warp/data may be copied into the Burns module.

## Phase 1 — downstream preserved RED

1. Add `scripts/check_context_fabric_burns_module_contract.py` as the permanent end-to-end consumer contract.
2. The script must accept/discover two external inputs supplied by CI: reviewed CUC directory and the installed pinned Context-Fabric consumer.
3. Build the reviewed CUC index through the public verification gate.
4. Dynamically choose a real CUC line/word from the verified index; generate synthetic `WorkbookRecord` rows only.
5. Normalize, align, build, report, and write the Burns feature-only module through production public APIs.
6. Load the CUC base alone through `CorpusManager` and record `max_slot`, `max_node`, and complete node-type counts.
7. Require `CorpusManager.load([cuc, burns_module], name='cuc-with-burns')` to load one logical composed corpus.
8. Require the composed `CorpusInfo`/API to preserve the base structural counts and expose all six Burns features.
9. Exercise both:
   - direct supported feature access (`api.Fs('burns_annotations')` / projection values), and
   - an MCP-supported search path (`cfabric_mcp.tools.search`) using a Burns projection constraint on the selected real CUC node type.
10. Assert the Burns output inventory contains only the six `burns_*.tf` files plus `burns-module-report.json`, with no `otype.tf`, `oslots.tf`, `otext.tf`, or copied CUC features.
11. Extend the reviewed-CUC workflow to check out/install the exact currently pinned Context-Fabric commit and run this script.
12. Freeze the RED commit and preserve CI evidence that the failure is at the current `CorpusManager.load()` single-path boundary.

## Phase 2 — minimal consumer GREEN

Use the same #28 researched contract for the coordinated `alexsosn/context-fabric` change. Issues are disabled there, so #28 remains the canonical ticket.

1. Branch from exact Context-Fabric master/pin `3a38ca80e617d872ce1664e0f0740486d0e7e8ac`.
2. Before production changes, add consumer tests that require:
   - existing `str` path remains supported;
   - `Path` scalar is supported;
   - ordered list/tuple of paths reaches core Fabric in order;
   - empty iterable fails explicitly;
   - missing location fails explicitly;
   - non-directory location fails explicitly;
   - default corpus name remains derived from first/base location;
   - multiple separately loaded corpora still work.
3. Preserve the consumer RED on the exact pre-change branch head.
4. Change only `cfabric_mcp/corpus_manager.py` unless tests prove another file is required.
5. Normalize input to a non-empty ordered tuple of resolved `Path`s and pass `[str(path) ...]` directly to `cfabric.Fabric(locations=...)`.
6. Keep single-path behavior backward compatible.
7. For `CorpusInfo.path`, use the single resolved path for scalar input and a deterministic joined representation for multiple locations; do not introduce a new public result field in this ticket.
8. Run the relevant MCP/core tests on the exact head.
9. Perform a logically independent adversarial review of the consumer PR. Fix any blocker through a new RED where appropriate.
10. Merge only after exact-head checks/review are green.

## Phase 3 — downstream GREEN

1. Update the immutable Context-Fabric pin in `.github/workflows/test.yml` and the reviewed-CUC composition workflow to the independently reviewed consumer merge commit.
2. Run the preserved downstream contract unchanged except for the pin/install wiring required to consume the fixed version.
3. Require exact-head success for:
   - Python 3.10/3.12/3.13 + installed-package checks;
   - Agora contract;
   - generic pinned Context-Fabric contract;
   - exact reviewed-CUC Text-Fabric composition;
   - exact reviewed-CUC + Burns through cfabric-mcp composition.
4. Record environment/pin evidence already provided by CI.

## Phase 4 — frozen-head adversarial review

Review downstream PR from scratch against #28/#21:

- no copied CUC warp/data;
- exact consumer pin;
- one logical corpus from two locations;
- base structural identity unchanged;
- Burns feature inventory visible;
- real consumer search/access path exercised;
- ordering/feature precedence not weakened;
- synthetic Burns only;
- no hidden fallback to standalone Burns corpus;
- exact-head CI green.

Merge only with expected-head protection and close #28. #29 remains downstream until this gate is complete.
