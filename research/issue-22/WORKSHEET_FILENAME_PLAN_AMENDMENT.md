# Plan amendment: prefixed worksheet basenames

This amendment follows `WORKSHEET_FILENAME_AMENDMENT.md` after the real-source GREEN audit failed on the first actual file basename.

## RED

Before production changes, add a focused synthetic regression that requires:

1. `DNs Worksheet 1.pdf` and `DNs Worksheet 1.csv` under the same workbook directory to produce the same extensionless `worksheet_id`;
2. row and annotation IDs to remain adapter-neutral for that pair;
3. the full prefixed stem to remain in `worksheet_id` rather than being normalized to bare `Worksheet 1`;
4. a terminal `Worksheet 1` token to be required, so trailing text such as `DNs Worksheet 1 copy.pdf` fails closed;
5. missing/out-of-range worksheet numbers to remain invalid.

Preserve the failing test evidence before implementation.

## GREEN

Change only the worksheet-basename recognition in `src/ugarit_context_parsing/annotations.py`: parse worksheet number from a terminal `Worksheet <1-5>` suffix while preserving the entire extensionless stem verbatim. Do not change identity serialization, semantic status, loaders, graph, CLI, or current standalone materialization.

## Verification

After the focused regression becomes green:

- require the full Python 3.10/3.12/3.13 + Agora + Context-Fabric contract workflow;
- rerun the checksum-pinned 45-Workbook production normalization audit;
- require 13,857 source records, 10,419 semantic annotations, and the corrected semantic-status counts;
- remove the temporary real-source workflow bookkeeping before final frozen-head review;
- run a fresh logically independent adversarial review on the final exact head.
