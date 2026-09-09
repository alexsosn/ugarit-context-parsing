# Plan: fix wrapped-headword/root ambiguity (#31)

## Preconditions

- Parent research: `research/issue-31/RESEARCH.md`.
- Base: `master@13806538df8a2e0fdcb8d45896e18cbb7a328a37`.
- Real-source audit: run `34355462989`, green including privacy/lifecycle guard.
- No Burns-derived lexical/source payload may be committed or uploaded.

## Step 1 — make row assembly directly testable without behavior change

Extract the state-machine portion of `parse_pdf()` into a pure helper operating on `list[tuple[int, dict[str, str]]]` plus workbook-role input. Keep `parse_pdf()` responsible for opening the PDF, computing bounds, calling `_content_lines()`, deriving the workbook ordinal, and finalizing rows.

The extraction must be covered by existing synthetic PDF tests and a direct equivalence test. It must not alter output by itself.

## Step 2 — RED first

Add a dedicated parser-state test module using synthetic cell dictionaries only.

Preserve RED evidence for the known structural failure:

- workbook VII role;
- A-bearing anchor opens a headword;
- next line is A-only;
- following row is another A-bearing anchor;
- expected: A-only text extends the current headword and does not populate `root`;
- baseline/current logic: the A-only text becomes `root`.

Add controls that should already pass or define unchanged behavior:

- same local shape under workbook IX becomes a root label for the following form;
- blank-A next anchor preserves current wrap behavior;
- unmatched bracket continuation preserves current wrap behavior;
- page boundary does not break an otherwise valid wrap;
- section banner clears root grouping;
- unknown workbook role plus ambiguous A-only line raises a structural error rather than guessing;
- non-ambiguous input with unknown role still parses normally;
- ordinal parser accepts Arabic and Roman 1–9 prefixes and rejects unrelated directory names.

Commit RED before production behavior changes.

## Step 3 — GREEN implementation

Implement only the smallest source-grammar change required:

1. derive workbook ordinal from the canonical parent-directory prefix;
2. pass it into the pure row assembler;
3. preserve definite-wrap logic first;
4. for residual ambiguous A-only lines:
   - IX => root;
   - I–VIII + open headword => wrap;
   - I–VIII without open headword => explicit structural error;
   - unknown role => explicit structural error.

No lexical exception list and no exact worksheet filename checks.

## Step 4 — regression and source-safe validation

Run:

- dedicated parser-state tests;
- full unit suite;
- Python 3.10/3.12/3.13 matrix;
- existing PDF determinism/materialization tests;
- Agora contract;
- Context-Fabric contract.

Use a source-safe aggregate-only verification against all 45 checksum-pinned Workbooks after implementation. It may report only counts/booleans. Required result:

- zero residual current-root classifications outside workbook IX under the new rule;
- Workbook IX root-candidate population remains structurally accounted for;
- no source payload persists.

## Step 5 — remove research instrumentation

Before final review:

- delete `.github/workflows/research-a-only-31.yml`;
- delete `research/issue-31/audit_a_only_lines.py` unless retained as an explicitly local research helper without automatic workflow (default: delete both);
- restore `tests/test_ci_action_pins.py` to the permanent 5 checkout / 3 setup-python contract;
- preserve aggregate evidence only in `RESEARCH.md` and PR/issue discussion.

Require a fresh standard CI run after this cleanup.

## Step 6 — logically independent adversarial review

Freeze one exact final head and re-derive the acceptance criteria independently. Review specifically for:

- accidental lexical/source-specific hard-coding;
- ordinal parsing that could misidentify unrelated directory names;
- Workbook IX genuine roots being converted to wraps;
- non-IX ambiguous lines silently becoming roots;
- changed behavior in reference/comment continuation;
- state leakage across sections/pages;
- parser API regressions for installed-package use;
- temporary workflow/action-pin bookkeeping left behind;
- restricted source data in the diff/logged artifacts;
- test fixtures that accidentally encode real Burns wording.

Only after no blocking findings and green CI on the reviewed frozen head: mark ready and merge with `expected_head_sha`.

## Definition of done

- Known Workbook VII wrapped-headword structural case is fixed without lexical hard-coding.
- Genuine Workbook IX root grouping remains supported.
- Ambiguity with unknown source role fails closed.
- All existing materialization/consumer behavior remains green.
- Temporary research instrumentation is gone.
- Independent adversarial review is attached to the frozen final commit.