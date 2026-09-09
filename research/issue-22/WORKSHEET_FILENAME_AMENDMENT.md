# Research amendment: real worksheet basenames carry workbook prefixes

The production real-Workbooks normalization audit exposed a false assumption in the original #22 worksheet-path grammar. The initial synthetic contract used basenames such as `Worksheet 1.pdf`, but the checksum-pinned Burns source contains real basenames such as `DNs Worksheet 1.pdf`.

This is not a source-adapter discrepancy: `scripts/parse_workbooks_to_csv.py` preserves each PDF relative path and changes only its final suffix to `.csv`, so PDF and generated-CSV adapters retain the same prefixed stem. Adapter-neutral identity therefore still works by removing only `.pdf`/`.csv`; the mistake was requiring the remaining stem to equal `Worksheet <n>` exactly.

## Corrected grammar

For a safe relative path below a validated workbook directory:

- the final suffix must remain `.pdf` or `.csv` case-insensitively;
- the extensionless basename is preserved **verbatim** as part of `worksheet_id`;
- `worksheet_number` is parsed only from a terminal token `Worksheet <n>` where `n` is 1–5;
- arbitrary source-authored prefix text before that terminal token is allowed and remains identity-bearing provenance;
- text after the terminal `Worksheet <n>` token is rejected;
- missing/out-of-range worksheet numbers remain rejected;
- no basename rewriting, prefix stripping, case-folding, or guessed workbook abbreviation mapping is introduced.

Examples:

- `01 Workbook I - Divine Names (DNs)/DNs Worksheet 1.pdf` is valid and has worksheet ID `01 Workbook I - Divine Names (DNs)/DNs Worksheet 1`;
- the corresponding `.csv` path has the same worksheet ID and stable row/annotation IDs;
- `.../DNs Worksheet 1 copy.pdf`, `.../DNs Worksheet.pdf`, and `.../DNs Worksheet 6.pdf` fail closed.

## TDD consequence

Add a regression before changing production code. It must prove that a prefixed real-shaped PDF/CSV pair converges to the same logical worksheet identity and stable IDs while malformed trailing text is rejected. The real-source audit remains the higher-level acceptance gate and must then reproduce 13,857 rows -> 10,419 semantic annotations with the corrected semantic-status counts.
