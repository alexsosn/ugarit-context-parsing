# Research: wrapped headword vs root labels (#31)

## Problem boundary

`scripts/parse_workbooks_to_csv.py::parse_pdf()` currently classifies every A-only line through one local heuristic. A line is treated as a wrapped headword only when the current state is `ANCHOR_A`/`WRAP` and either the following anchor has blank A or bracket balancing proves continuation. Every other A-only line becomes a persistent `root` value.

That local geometry is insufficient: the known Workbook VII / Worksheet 1 wrapped-headword case has the same immediate shape as a genuine Workbook IX root label: an open A-bearing headword/form, then an A-only line, then another A-bearing anchor.

## Source semantics

The parent #21 research established that root grouping is a structural convention of Workbook IX (Cultic Actions), where verbal forms are grouped under roots. The other workbook categories do not use that root-grouping layer.

Therefore root-vs-wrap is not purely a neighboring-row geometry problem. Workbook role is part of the source grammar.

## Aggregate-only real-source audit

PR #33 ran `Issue 31 A-only structural audit` on the checksum-pinned Workbooks source in runner-temporary storage. Run `34355462989` / job `102478890816` completed successfully, including the no-persistence guard. No Burns lexical values, rows, references, comments, CSV, or TF payload were emitted.

Observed across all 45 PDFs:

- workbook directories: 9;
- PDFs: 45;
- every canonical workbook directory has a leading Arabic or Roman ordinal;
- parsed directory ordinals are exactly 1 through 9;
- current root candidates by workbook: I–VI = 0, VII = 1, VIII = 0, IX = 276;
- the sole non-IX candidate is openable (`ANCHOR_A`/`WRAP`) and followed by a new A-bearing anchor;
- all 276 Workbook IX root candidates are also followed by a new A-bearing anchor;
- 141 Workbook IX root candidates occur while the local state is openable.

The first version of the audit had a bad lifecycle assertion (`test ! -e output`) against a repository path that already exists. The actual audit step succeeded. The guard was corrected to test only audit-created restricted paths, and the complete rerun above is green.

## Consequences

1. Looking at the next row cannot distinguish the false positive from genuine roots: both use the same local shape.
2. `prev_kind` alone cannot distinguish them either: 141 genuine Workbook IX roots are locally openable.
3. Root eligibility must be derived from workbook role.
4. The canonical source tree provides a non-lexical role discriminator: workbook ordinal encoded in the parent directory prefix.
5. No Burns headword/root string or exact worksheet filename needs to be hard-coded.

## Proposed parser contract

Introduce a small helper that derives a workbook ordinal from a canonical parent-directory prefix, supporting Arabic `1..9` and Roman `I..IX` forms.

Extract the post-geometry row assembly into a pure helper accepting the content-line sequence plus an optional workbook ordinal. `parse_pdf()` remains the pdfplumber/geometry adapter and supplies the derived ordinal.

For an A-only line:

1. Preserve the current *definite wrap* rules first (blank-A next anchor or bracket continuation).
2. For a residual ambiguous A-only line:
   - workbook IX: treat it as a root label;
   - workbooks I–VIII with an open current headword: append it to the headword as a wrap;
   - workbooks I–VIII without an open current headword: fail closed as structurally unexpected;
   - unknown workbook role: fail closed for the ambiguous line rather than silently guessing root vs wrap.

This keeps established Workbook IX roots intact and fixes the one measured false-positive shape outside IX.

## Scope boundaries

- Do not change PDF geometry, column boundaries, transliteration repair, PN repair, corrections, KTU/reference handling, comments, or materialization.
- Do not hard-code source lexical strings.
- Do not make #22 normalization changes here.
- The temporary real-source audit workflow/script is research instrumentation and must be removed before final PR review; its aggregate findings remain in this file.
- Restore the permanent action-pin contract from 6 temporary checkout uses to the repository baseline of 5 after removing the audit workflow.

## Validation requirements

Synthetic tests must cover:

- the measured false-positive shape in a non-IX workbook: `ANCHOR_A -> A-only -> A-bearing ANCHOR` becomes one continued headword, not a root;
- the same local shape in workbook IX remains a genuine root transition;
- existing blank-A wrap behavior;
- existing bracket-closing wrap behavior;
- page-boundary wrap behavior;
- section reset;
- unknown workbook role fails closed only when an ambiguous A-only line requires the role decision;
- ordinal parsing supports canonical Arabic and Roman prefixes and rejects unrelated names.

After GREEN, all existing Python matrix, PDF determinism/materialization, Agora, and Context-Fabric gates must remain green.