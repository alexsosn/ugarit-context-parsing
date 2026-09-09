# Research amendment: semantic grouping requires explicit source-row continuity

An adversarial pass against parent `CONTIGUOUS_GROUPING_AMENDMENT.md` found one remaining ambiguity in the #22 research contract.

`WorkbookRecord` inputs are normally emitted in stable worksheet/source-row order, but production semantic grouping cannot define "contiguous" as merely "adjacent in the supplied iterable". A caller may provide an incomplete sequence, or an earlier validation/filtering bug may omit a row. In that case source rows 1 and 3 with the same worksheet/textual key are adjacent in memory but are **not** one authored merged-cell run.

## Corrected grouping rule

Two normalized source records may remain in the same `BurnsAnnotation` only when all of the following hold:

1. their canonical `worksheet_id` values are equal;
2. the shared authored textual key is equal: `section`, `root`, `headword`, `ktu`, `references`;
3. the next record has `source_row == previous.source_row + 1`.

A gap in `source_row` flushes the current annotation even if every scholarly field is otherwise identical.

Within one worksheet, normalization must also reject source rows that move backwards or repeat a row locator. It must not silently sort caller input because supplied order and row adjacency are provenance. A new worksheet may restart at source row 1.

## Consequences

- `row 1, row 3` with the same textual key -> two annotations.
- `row 1, row 2` with the same textual key -> one annotation.
- `row 2, row 1` in the same worksheet -> normalization error.
- duplicate logical row IDs/locators remain an error under the existing identity contract.
- worksheet transitions always flush grouping and reset the row-continuity sequence.

This correction is source-domain only. It does not add reference parsing, CUC lookup/alignment, TF output, or any change to the current standalone materializer.
