# Plan amendment: RED/GREEN gate for source-row continuity

This amendment follows `CONTINUITY_RESEARCH_AMENDMENT.md` and supersedes the narrower wording in `PLAN.md` that grouping may rely only on supplied adjacency plus textual-key equality.

## RED before GREEN

Add tests before `annotations.py` implementation requiring:

1. same worksheet + same textual key + source rows 1 and 3 produce **two** annotations because the source-row run has a gap;
2. same worksheet + same textual key + source rows 1 and 2 still produce one annotation;
3. same worksheet source rows that move backwards fail with `BurnsNormalizationError` rather than being sorted;
4. a worksheet transition may restart source-row numbering and always starts a new annotation.

These tests are additive to the existing RED suite; the intended RED reason remains the missing `ugarit_context_parsing.annotations` production seam until GREEN begins.

## GREEN constraint

The contiguous grouping helper must track both previous grouping key and previous source-row locator. It may extend a group only for an equal key with `source_row == previous_source_row + 1`. It must preserve input order and fail closed on backwards/non-monotonic rows within one logical worksheet.

Do not add sorting, global grouping, source-row repair, CUC knowledge, or adapter-specific branches to satisfy this gate.

## Review addition

The frozen-head adversarial review must explicitly challenge missing-row and out-of-order inputs, not just the `A, B, A` non-contiguous-key case.
