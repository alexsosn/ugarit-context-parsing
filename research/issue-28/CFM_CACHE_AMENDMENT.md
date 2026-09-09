# Post-RED research amendment: Context-Fabric `.cfm` cache and multi-location corpora

The first consumer GREEN head (`alexsosn/context-fabric@71b95eb23ab2ca1425855041e426bcda32d9c80a`) successfully normalized and passed ordered locations into core `cfabric.Fabric`, but exact downstream execution exposed a second blocker that invalidates the original research assumption that core requires no change.

## Evidence

Downstream workflow run `34395587325`, job `102614373712`, checked out the exact consumer head and ran the newly committed consumer tests.

Result: 4 tests passed and 2 composition tests failed. `CorpusManager` logged both locations and loaded the base structure successfully, but the temporary feature-only `module_label.tf` was absent from `CorpusInfo.node_features` and `api.Fs('module_label')` returned `None`.

The failure is caused by Context-Fabric's `.cfm` fast path:

1. a prior scalar/base `Fabric.loadAll()` auto-compiles the base corpus to `.cfm`;
2. a later `Fabric(locations=[base, module]).loadAll()` calls `load('')`;
3. `load()` detects the base `.cfm` and constructs the API from that cache;
4. `loadAll()` then loads only node/edge features listed in the cached base `.cfm` metadata;
5. feature files discovered from the additional module location are never loaded.

This is unsafe for any composed corpus, not Burns-specific. A cache compiled for one location cannot be treated as authoritative for a different multi-location composition unless the cache identity includes the complete ordered composition.

The real #28 contract intentionally loads CUC base-only before CUC+Burns, so this is a production blocker, not an artificial test-order artifact.

## Revised narrow design

Preserve the MCP adapter change, but add a minimal core safety rule: the current single-corpus `.cfm` cache fast path must not be used when a `Fabric` instance represents a multi-location (or otherwise composition-distinct) corpus unless the cache is explicitly proven to represent that exact composition.

For this ticket the conservative compatible behavior is:

- use existing `.cfm` acceleration for the historical single-location/default-module case;
- bypass `.cfm` detection/auto-compilation for multi-location composition and load the `.tf` feature union directly;
- preserve ordered feature precedence from `_makeIndex()`;
- do not delete or mutate an existing base `.cfm` cache;
- do not invent a composite cache format/manifest in this ticket.

A richer composition-aware `.cfm` cache identity can be a later performance ticket.

## Required focused RED before core change

Add an isolated core test that copies the mini corpus to a temporary base directory, performs a base-only `loadAll()` so a `.cfm` cache exists, creates a separate feature-only module directory, then requires `Fabric(locations=[base, module]).loadAll()` to expose the module feature while preserving base warp counts. The test must also prove the base `.cfm` still exists and is not deleted as a workaround.

Only after this RED is preserved may core cache selection change.