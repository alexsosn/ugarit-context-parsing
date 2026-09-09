# Research amendment: contiguous semantic grouping is required

A source-safe real-Workbooks audit on PR #25 tested the identity concern raised in `SOURCE_RECORD_IDENTITY_AMENDMENT.md`: whether global value deduplication accidentally merges separate authored entries that happen to have the same `(worksheet, section, root, headword, KTU, references)` values.

## Evidence

Temporary research workflow `Burns contiguous grouping audit`, run `34339879020`, used the repository's checksum-pinned Workbooks source in runner-temporary storage and emitted aggregate counts only.

It observed:

- PDFs: **45**;
- raw parser rows: **13,857**;
- global unique value keys: **10,415**;
- contiguous authored groups: **10,419**;
- value keys repeated non-contiguously: **4**;
- extra groups lost by global deduplication: **4**;
- maximum contiguous runs for one repeated key: **2**.

The audit intentionally exited non-zero when the two partitions differed. That failure is research evidence, not a product regression: it demonstrates that the earlier `10,415 semantic annotations` figure from the aggregate probe was a global-key heuristic and under-counted the correct contiguous source grouping by four annotations.

## Contract consequence

Production normalization in #22 must **not** collapse records globally by scholarly field values. A semantic Burns annotation is one contiguous authored run inside one logical worksheet. A later non-contiguous run with identical scholarly values is a distinct annotation with a distinct stable annotation ID.

The corrected real-source lower-bound semantic-group count for the current parser output is therefore **10,419**, while 10,415 remains useful only as documentation of the historical global-dedup research heuristic.

Source-row provenance remains lossless and ordered inside each group. The production grouping implementation must additionally use explicit source-row continuity, not merely adjacency in whatever input iterable happens to be supplied.

## Privacy / lifecycle

The audit printed no Burns field values and persisted no generated source dataset. Its temporary workflow/script exist only to establish this research fact and are not part of the intended product or permanent CI surface; after recording this amendment they should be removed and the standard action-pin contract restored before the parent research PR is finalized.
