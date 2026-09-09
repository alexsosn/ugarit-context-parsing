# Plan amendment: direct state-machine seam is sufficient

The RED implementation showed that an extra production extraction is unnecessary. `parse_pdf()` already has a source-safe structural seam: tests can mock only `_content_lines()` and PDF geometry while exercising the real row-assembly state machine end-to-end.

This supersedes PLAN Step 1's proposed extraction of a separate row-assembly helper. Adding that refactor now would enlarge the production diff without improving the RED/GREEN evidence.

GREEN therefore stays minimal:

1. add a workbook-ordinal parser derived only from the canonical parent-directory prefix;
2. compute the ordinal once in `parse_pdf()`;
3. preserve current definite-wrap branches unchanged;
4. change only the residual A-only ambiguity decision according to the researched workbook-role contract;
5. add the remaining direct structural controls (ordinal parsing, unknown-role fail-closed, page boundary, section reset).

The frozen-head adversarial review must treat avoiding the unnecessary extraction as a scope-reduction decision, not as omitted testability: the preserved RED run `34356460070` already exercised the real state machine and failed exactly at the intended behavior.