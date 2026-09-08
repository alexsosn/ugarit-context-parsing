# Independent review amendment: source-root independence for CSV determinism (#3)

## Finding

The first evidence candidate materialized the same source directory twice. That proves repeatability at one absolute path, but Agora's planned request-identity cache deliberately excludes machine-local source paths and binds canonical source content/tree identity instead.

If a converter accidentally embedded its absolute source root into scholarly output, two byte-identical source trees at different machine paths could have the same intended Agora source identity but different converter output. A same-path replay would miss that defect.

Current converter code inspection indicates the absolute root is not emitted: source features use relative `source_file`, the source tree hash uses relative paths + bytes, and the report contains no root path. For cacheability evidence, however, this should be demonstrated rather than inferred.

## Required strengthened evidence

The repeated-materialization test must use **two distinct absolute source roots** whose canonical relative file trees and file bytes are identical.

To exercise both relevant invariants at once:

1. source A creates the lexically later worksheet before the earlier worksheet;
2. source B creates the same files in the opposite creation order;
3. relative-path + file-byte source snapshots for A and B must be exactly equal before conversion;
4. materialize A -> output A and B -> output B through the real CSV CLI/writer;
5. verify both source snapshots remain unchanged after conversion;
6. retain the existing exhaustive `.tf` comparison modulo only `@dateWritten`, complete report equality, independent `loadAll()` comparison, and full navigation/feature checks.

This proves that neither absolute root spelling nor filesystem creation order leaks into the cache-relevant scholarly output for the reviewed execution identity.

## Gate interpretation

This is a review-driven strengthening of an evidence test, not evidence of a known production bug. The already-green Python 3.13 result at `60af75d48623bac0b6dfdfc7151aefc444aeab98` remains useful historical evidence for same-path repeatability but is no longer sufficient for final cacheability review.

The strengthened exact head must rerun the full Python 3.10/3.12/3.13 + Agora contract matrix. If distinct source roots produce additional differences, that failure becomes a genuine RED requiring research before any production fix or normalization change.
