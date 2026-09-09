# Research: Context-Fabric CUC + Burns module composition (#28)

## Scope

Issue #28 follows the merged feature-only Burns module work from #27. The required consumer shape is one logical corpus composed from:

1. the exact reviewed CUC 0.2.8 Text-Fabric directory, which owns `otype`, `oslots`, `otext`, and CUC features; and
2. a separate Burns module directory, which owns only the six `burns_*` node features emitted by `write_burns_module()`.

Copying the CUC warp/data into the Burns directory is explicitly out of scope and would violate the architecture established by #21/#27.

No Burns-derived fixture or artifact may be committed or uploaded. Integration evidence must use public CUC plus synthetic Burns rows.

## Existing local evidence

The permanent reviewed-CUC workflow already proves the feature-only Burns module composes correctly with upstream Text-Fabric by loading:

```python
Fabric(locations=[str(cuc), str(output)], modules=[''], silent='deep')
```

and checking unchanged CUC `maxSlot`, `maxNode`, node-type vector, line navigation, and Burns payload discovery on real CUC nodes.

The existing `context-fabric-contract` job is different: `scripts/check_context_fabric_contract.py` materializes the old standalone synthetic corpus and calls:

```python
CorpusManager().load(str(output), name='burns-synthetic')
```

It proves general compatibility with Context-Fabric/cfabric-mcp, but it does not exercise feature-module composition.

## Exact consumer pin

The repository currently pins Context-Fabric at:

`alexsosn/context-fabric@3a38ca80e617d872ce1664e0f0740486d0e7e8ac`

That commit is also current `context-fabric/master` as researched on 2026-09-09.

## Core Context-Fabric already supports the required model

At the exact pin, `cfabric.core.fabric.Fabric.__init__` declares:

```python
locations: str | Iterable[str] | None
modules: str | Iterable[str] | None
```

It normalizes iterable locations independently. `_makeIndex()` walks `locations` in their supplied order and then `modules`; for duplicate feature names, the final discovered path wins. Therefore a feature-only second location is already a native core composition mechanism. The Burns module does not duplicate CUC feature names, so no override is expected.

No core Context-Fabric change is required for #28.

## cfabric-mcp loses the core capability

At the exact pin, `cfabric_mcp.corpus_manager.CorpusManager.load()` exposes only:

```python
path: str
```

and immediately does:

```python
path_obj = Path(path).expanduser().resolve()
...
CF = cfabric.Fabric(locations=str(path_obj), silent='deep')
```

This narrows the core API to one filesystem location. Passing `[base, module]` cannot reach `cfabric.Fabric`; `Path(list)` fails before corpus loading. The MCP layer therefore cannot currently represent one logical corpus composed from CUC plus a Burns module.

The existing MCP `test_multi_corpus.py` covers several separately loaded corpora and switching/search isolation between corpus names. It does not cover multiple locations contributing features to one corpus.

## CorpusInfo implication

`CorpusInfo` currently stores a single `path: str`. A minimal backward-compatible fix does not need to redesign this public result immediately: `CorpusManager` can retain the historical single path string when one location is supplied and use a deterministic display string for multiple locations. The composition contract itself should be proven through the stored `Fabric.locations`, API feature inventory, and actual MCP search/access behavior rather than by overloading `CorpusInfo.path` semantics more than necessary.

A richer structured `locations` field would be a separate API-evolution decision and is not required to unblock #28.

## Consumer-side tracking limitation

A consumer-side issue was attempted in `alexsosn/context-fabric`, but GitHub returned HTTP 410 because Issues are disabled in that repository. This fact is recorded on `ugarit-context-parsing#28`; no upstream issue number will be fabricated. #28 is the canonical blocker record for the coordinated consumer patch.

## Minimal consumer change

The narrowest compatible change is in `cfabric_mcp.CorpusManager.load()` only:

- accept `str | Path | Iterable[str | Path]` (excluding accidental scalar iteration of strings);
- normalize to a non-empty ordered tuple of resolved paths;
- validate every location exists and is a directory;
- preserve order and pass the resolved locations directly to `cfabric.Fabric(locations=[...])`;
- derive the default corpus name from the first/base location, preserving existing single-path behavior;
- preserve existing `features` handling and corpus cache/current semantics;
- provide deterministic/auditable location text to `CorpusInfo.from_api()` without copying files.

Core Fabric feature precedence must remain untouched.

## Required RED

Before changing the consumer, add a permanent downstream contract that uses the exact current consumer pin and requires:

1. checkout/build of the exact reviewed CUC base;
2. construction of a legal synthetic Burns source aligned to actual public CUC nodes;
3. writing of the feature-only Burns module through production `write_burns_module()`;
4. `CorpusManager.load([cuc_dir, burns_module_dir], name=...)` for one logical corpus;
5. Burns feature discovery through the returned MCP-supported API;
6. at least one real search/access path that constrains or returns a Burns feature;
7. unchanged CUC `maxSlot`, `maxNode`, and type counts compared with base-only Context-Fabric loading;
8. proof that the Burns output contains no CUC warp/diplomatic feature copies.

On the researched pin the RED should fail at the multi-location `CorpusManager.load()` boundary, before a composition workaround is possible.

## GREEN strategy

Implement and independently review the minimal Context-Fabric `CorpusManager` change. Then pin the downstream workflow to the reviewed consumer commit and rerun the exact real-CUC integration contract. The downstream pin must remain immutable; do not use a moving branch.

## Adversarial questions for final review

- Does a string still behave as one path rather than an iterable of characters?
- Are empty location lists rejected explicitly?
- Are missing/non-directory locations rejected before constructing Fabric?
- Is caller order preserved all the way into `Fabric.locations`?
- Can two independent corpora still be loaded/switched exactly as before?
- Does module composition accidentally duplicate or override `otype`/`oslots`?
- Are Burns features visible through real MCP-supported search/access rather than only raw core internals?
- Does the integration use public CUC and synthetic Burns content only?
- Is the downstream workflow pinned to the exact reviewed consumer commit?
