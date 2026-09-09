# Real-source validation: patched Workbook parser (#31)

After GREEN, the temporary source-safe audit was strengthened to run the patched production `parse_pdf()` over all checksum-pinned Burns Workbooks rather than merely re-counting the old heuristic.

## Evidence

Workflow run `34357179030`, job `102484718118`, tested branch head `bc6e04019a479de051ea583c4da8f639068b22aa` against base `e9a92f55fb95680e9beed4cdac2f14109a46494a`; CI provenance attested synthetic merge `9500c006a4e7cf075c3b1332d074ff015964275c`.

The production parser completed successfully on every source PDF and emitted aggregate-only evidence:

- PDFs parsed: **45**;
- workbook ordinals observed: **1–9**;
- total parsed rows: **13,857** (unchanged from the pre-fix corpus audit);
- root-bearing rows outside Workbook IX: **0**;
- root-bearing rows in Workbook IX: **3,078**;
- total root-bearing rows: **3,078**.

The workflow's no-persistence guard also passed: the downloaded `Workbooks` tree existed only in runner-temporary storage, and no audit JSON or Burns-derived row payload was written into the checkout.

## Interpretation

This validates the actual production parser boundary, not only synthetic tests:

1. the known non-IX false-positive root class disappears across all 40 non-IX worksheets;
2. Workbook IX still retains its authored root-grouping structure;
3. the parser's total row count remains unchanged, so the correction reclassifies authored A-column structure instead of adding or dropping source rows;
4. no source lexical values are needed in committed fixtures or review artifacts.

This file preserves the aggregate evidence. The temporary source-download workflow and audit script are not product/CI surface and must be removed before final review.