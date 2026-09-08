# Plan: legal synthetic real-parser PDF replay (#6)

## Goal

Prove repeated semantic determinism for `burns-workbooks-pdf-text-fabric` under one exact resolved environment using only ephemeral, programmatically generated synthetic PDFs and the complete comparator merged in #7.

No Burns-derived data or new PDF-generation dependency will be introduced.

## Preconditions

- Research: `research/issue-6/RESEARCH.md`.
- Baseline: post-#7 `master` at `f0c4e666fa9783b455ef3cc1b86238f41bb6e8b6`.
- Existing comparator: `ugarit_context_parsing._semantic_compare.compare_text_fabric_artifacts`.
- Existing CI environment-evidence step remains unchanged and already runs before the full suite on Python 3.10/3.12/3.13.

## Test isolation

Put all synthetic-PDF generator and replay code in a dedicated `tests/test_pdf_determinism.py`. The CSV integration replay remains untouched, avoiding coupling between two evidence contracts. Do not create a production PDF-generation API.

## Synthetic PDF generator

### `_pdf_escape(text)`

Escape backslash and parentheses for a PDF literal string.

### `_write_synthetic_pdf(path, text_items, vertical_lines=())`

Write deterministic PDF 1.4 bytes with exactly five indirect objects:

1. catalog;
2. pages tree;
3. one `842 x 595` page;
4. standard Type 1 Helvetica font dictionary;
5. content stream.

The content stream emits each `(x, y, text)` as a separate `BT ... Tj ET` operation and optional vertical `m/l/S` line operations. Construct the classic xref table from measured byte offsets. Emit no document metadata, timestamps, IDs, compression, embedded fonts, or external assets.

The helper creates parent directories and always writes the same bytes for the same arguments.

### `_write_pdf_determinism_fixture(root, later_first)`

Create the same two relative PDFs in either forward or reversed creation order:

- `Alpha/Ruled.pdf`: ten canonical vertical boundaries and synthetic rows exercising section state, legacy `\\zr` -> `ġzr`, A-only wrapped headword continuation, a new KTU row with blank A, a locus sub-row sharing KTU/headword cells, and a C/I continuation line.
- `Zeta/Fallback.pdf`: no rules, with a separate synthetic section/anchor row using KTU `1.16`.

All synthetic text is original test data.

## RED commit

Add `test_repeated_synthetic_pdf_materialization_is_semantically_identical` in `tests/test_pdf_determinism.py`.

The RED test must, before its deliberate failure:

1. create source A and source B with identical relative PDF bytes but opposite creation order;
2. snapshot relative file SHA-256 values and require A == B;
3. invoke the real CLI twice with `--input-format pdf` into fresh output directories;
4. require both conversions to return 0;
5. prove both source trees remain byte-identical and unchanged;
6. require `compare_text_fabric_artifacts(output_a, output_b) == ()`;
7. then call the planned but absent `_assert_synthetic_pdf_contract(self, output_a)` test helper.

At this exact commit, `_assert_synthetic_pdf_contract` must not exist. CI must therefore fail with a NameError only after both real PDF materializations and complete semantic equality have executed successfully. Preserve the exact failed run as RED evidence.

If either real materialization or the semantic comparator fails before the deliberate helper seam, stop and research that real failure instead of proceeding to GREEN.

## GREEN helper

Add only `_assert_synthetic_pdf_contract(testcase, output)` to `tests/test_pdf_determinism.py` unless RED exposed a production defect.

Load the output independently with real Text-Fabric and assert specific real-parser consequences so the fixture cannot pass while silently bypassing the intended PDF behaviors:

- four `record` slots;
- two worksheet nodes with navigation labels `Alpha/Ruled` and `Zeta/Fallback`;
- record `source_file` sequence `Alpha/Ruled.pdf` x3 then `Zeta/Fallback.pdf`;
- all `source_page` values are 1;
- headwords are `ġzr wrapped` for the three ruled records and `mlk` for fallback;
- KTU sequence is `1.14`, `1.15`, `1.15`, `1.16`;
- CUC sequence is `KTU 1.14`, `KTU 1.15`, `KTU 1.15`, `KTU 1.16`;
- shared/wrapped references are `I 1`, `II 2 continued`, `II 2 continued`, `III 3`;
- the third ruled record receives continuation comment `comment`;
- complete report status is `ok`, source format is `pdf`, source file count is 2, and record count is 4.

Run the helper against both outputs, not only one, after comparator equality.

### Post-RED evidence strengthening

The exact RED head `422d0e237321d9dffd9eabe4a6de85089c40ecc1` and run `34283572929` established that both real PDF materializations completed with four records and the complete comparator returned equality before the deliberate missing-helper `NameError`.

Before freezing GREEN for adversarial review, an evidence-scope challenge identified one gap in the original GREEN wording: downstream semantic equality alone cannot distinguish whether the ruled fixture used derived boundaries or happened to produce the same rows through canonical fallback. The GREEN test therefore also adds `_assert_pdf_geometry_contract()` as a test-harness-only strengthening. It opens each ephemeral synthetic PDF with real `pdfplumber`, requires exactly ten vertical edges for `Alpha/Ruled.pdf` and zero for `Zeta/Fallback.pdf`, and invokes the production `file_bounds()` function on both. This records direct evidence that the two intended geometry branches are reachable for the generated inputs while leaving production converter code unchanged.

This strengthening does not widen the determinism claim, add a PDF-specific ignore rule, or alter the already-preserved RED contract. The earlier “add only” sentence remains above as the pre-RED plan; this amendment documents the deliberate post-RED strengthening rather than rewriting that history.

## Test gates

For the final exact head require:

- full unittest suite on Python 3.10, 3.12, and 3.13;
- real installed-package parser verification outside checkout;
- successful `Record execution environment` step in all three test jobs;
- pinned Agora manifest-contract job;
- no generated PDF/TF artifacts uploaded or committed.

The source generator itself must be deterministic; source A/B snapshots are part of the test contract.

## Independent adversarial review

Freeze the final head and independently challenge:

1. Does the test call the default packaged PDF parser, or can an injected/mock parser satisfy it?
2. Do both synthetic PDFs pass through real `pdfplumber.open()` / word extraction?
3. Is ruled `file_bounds()` actually exercised by ten extractable vertical edges?
4. Is canonical fallback actually exercised by a file with no vertical edges?
5. Do the expected TF values prove wrapped/merged-row assembly and legacy transliteration repair happened?
6. Does KTU -> CUC normalization come from the common production graph rather than the fixture helper?
7. Are source roots byte-identical and created in opposite order?
8. Does the complete #7 comparator cover all persisted/loaded semantics with no PDF-specific ignore expansion?
9. Is the PDF generator independent of Burns content and free of bundled external font/assets?
10. Does environment evidence include the resolved `pdfplumber`/`pdfminer.six` dependency closure through the full installed distribution set?
11. Does wording avoid claiming cross-environment PDF determinism?

Any blocker starts a focused regression/research sub-loop and requires fresh exact-head CI/review.

## Definition of done

- research -> plan -> exact RED -> GREEN history is preserved;
- both real PDF materializer runs complete before the deliberate RED seam;
- deterministic legal synthetic PDFs exercise ruled and fallback geometry plus wrapped/merged row logic, transliteration repair and CUC normalization;
- complete semantic comparator returns equality;
- specific expected parsed/TF semantics are asserted for both artifacts;
- Python 3.10/3.12/3.13 plus environment and Agora gates are green at frozen head;
- independent adversarial review finds no blocker before merge.
