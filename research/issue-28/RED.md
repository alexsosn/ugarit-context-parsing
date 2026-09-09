# Preserved RED: Context-Fabric CUC + Burns composition (#28)

Exact downstream RED head: `8bbe56f914988c1b0030908d7f89f738af9344a7`.

Workflow run: `34394954198` (`Context-Fabric Burns module contract`).
Job: `102612236144` (`context-fabric-burns-module`).

The RED is causal and occurs at the researched consumer boundary.

Successful before the failure:

- CI provenance verified the PR merge test head/base;
- exact reviewed public CUC commit `ad69400f5446e1c8217af01659c7c10ab00c015b` checked out;
- exact Context-Fabric consumer commit `3a38ca80e617d872ce1664e0f0740486d0e7e8ac` checked out;
- producer plus `context-fabric==0.5.7` and `cfabric-mcp==0.1.7` installed successfully;
- execution environment and exact consumer/CUC pins recorded;
- reviewed CUC index construction and synthetic Burns source/module path completed;
- the feature-only Burns module was written through production code;
- `CorpusManager.load(str(cuc), name='cuc-base')` succeeded and reported 5 node types / 16 node features / 0 edge features.

The first failing operation is the required one-logical-corpus/two-location call:

```python
corpus_manager.load(
    [str(cuc), str(output)],
    name='cuc-with-burns',
)
```

Exact failure from installed `cfabric_mcp/corpus_manager.py` line 54:

```text
path_obj = Path(path).expanduser().resolve()
TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'list'
```

Therefore the RED proves the producer and base consumer path work, while the current MCP adapter cannot express the multi-location composition already supported by core Context-Fabric. No CUC-copy workaround is permitted.

Next gate: implement the minimal consumer-side fix under the frozen #28 research/plan, with its own preserved consumer RED before production changes.
