# Review amendment: CUC 0.2.8 tablet count

A pre-final adversarial review found a count discrepancy in the pinned CUC base at `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`.

## Evidence

- `tf/0.2.8/otype.tf` assigns `tablet` to nodes `153968–154246`, which is **279** nodes inclusive.
- `tf/0.2.8/tablet.tf` supplies a sequential tablet-label feature across that range.
- CUC `README.md` says **278 tablets** are currently available.

The exact TF warp is authoritative for downstream node-ID compatibility. The Burns module fingerprint/index must therefore assert **279 tablet nodes** for this reviewed revision. The README's 278 figure may describe a stale or different semantic count, but it must not be used to mutate, filter, or reinterpret the warp.

The connected GitHub integration cannot open issues in `DT-UCPH/cuc` (403). Local issue #30 tracks rechecking/reporting this upstream during #23.

This amendment supersedes the parent research sentence that repeats “CUC currently contains 278 tablets” as though it were an exact dataset count. It remains valid to use the README's published KTU range list as descriptive coverage evidence, but compatibility assertions come only from the pinned TF files and their fingerprints.
