# Research: real-parser PDF determinism evidence (#6)

## Question

Can the Burns PDF materializer be exercised reproducibly without redistributing any Burns-derived PDF/content, and what smallest synthetic fixture proves the actual packaged `pdfplumber` extraction path rather than an injected parser seam?

## Baseline

- `master`: post-#7 CSV evidence merge (`f0c4e666fa9783b455ef3cc1b86238f41bb6e8b6`).
- `burns-workbooks-pdf-text-fabric` calls `load_pdf_directory()`, whose default parser is `parse_workbook_pdf()`, which imports the repository's packaged `scripts.parse_workbooks_to_csv.parse_pdf` implementation.
- The parser uses real `pdfplumber.open()`, `page.extract_words()`, page-edge geometry, deterministic word sorting, Workbook row-state assembly, transliteration repair, and then the common TF graph/report/writer path.
- #5/#7 already provides `compare_text_fabric_artifacts()` covering the complete persisted TF/report surface plus loaded nodes, node features, edge targets/values, and navigation.
- CI now records Python/platform/resolved-distribution evidence plus an environment digest after dependency installation and before the test suite.

No converter production change is expected unless the real-parser replay exposes a genuine semantic difference.

## Legal fixture design

Do not use, crop, trace, encode, quote, or otherwise derive fixture bytes/text/layout from Burns PDFs. Generate a tiny PDF from original synthetic strings and deliberately simple test geometry.

The fixture can be produced with Python standard-library code only. A minimal PDF 1.4 file needs a catalog, pages tree, page, font dictionary, content stream, classic cross-reference table, trailer, and correct object byte offsets. Text can use PDF's standard Type 1 `Helvetica` font without embedding a font program. Adobe's PDF 1.4 reference documents both the classic cross-reference structure and Helvetica among the standard 14 Type 1 fonts.

This avoids:

- a committed binary fixture;
- a new runtime or test-only PDF-generation dependency;
- font-file redistribution/licensing concerns;
- generator timestamps, random IDs, or metadata that would make source bytes unstable.

The test generator should write deterministic bytes directly into temporary source directories. It must escape PDF literal-string backslashes/parentheses and calculate cross-reference offsets from the final byte stream.

## Geometry verified for the proposed fixture

A one-page `842 x 595` PDF using built-in Helvetica and text placed around PDF y=410..310 is extracted by `pdfplumber` with `top` around 177..277, safely below the parser's `HEADER_BAND_TOP=145` exclusion band.

The parser's canonical x boundaries are:

`69, 166, 197, 296, 373, 438, 504, 553, 574, 772`

Synthetic text at x≈80/175/210/310/380/600 is therefore classified into Workbook columns A/B/C/D/E/I as intended.

For a ruled fixture, emit ten vertical line operators at those boundary x positions. `pdfplumber` exposes them as vertical edges, and `file_bounds()` derives exactly ten collapsed boundaries, exercising the ruled-page branch.

For a fallback fixture, emit no vertical edges. `file_bounds()` then uses `CANONICAL_BOUNDS`, exercising the no-ruling fallback with the same legal generator.

A local prototype with `pdfplumber` confirmed that a row sequence containing:

- A=`\\zr`, B=`1.14`, C=`I 1`, D=`GP`, E=`1`;
- an A-only `wrapped` line;
- a headwordless B=`1.15`, C=`II 2`, D=`PH`, E=`2` row;
- a further headwordless locus row D=`PH`, E=`3`;
- a C-only continuation plus I=`comment`;

is extracted and assembled by the real parser into three rows. The legacy ASCII backslash survives PDF text extraction and `fix_ugaritic()` converts it to `ġ`, yielding the synthetic headword `ġzr wrapped`. The second/third rows share the wrapped headword and KTU grouping; the continuation updates the shared references/comment state. This exercises the parser's merged/wrapped-row machinery without using source text.

## Two-file source tree

Use two one-level PDF paths in each source root, for example:

- `Alpha/Ruled.pdf`: ruled geometry plus the richer wrapped/merged row sequence above, including `1.14`/`1.15` and legacy `\\zr`.
- `Zeta/Fallback.pdf`: no vertical rules and a short independent synthetic section/row such as headword `mlk`, KTU `1.16`, references `III 3`, locus `GP`, room `4`.

Create the files in opposite order in two distinct absolute source roots while keeping relative paths and PDF bytes identical. This simultaneously exercises deterministic `*/*.pdf` traversal, source-root independence, and source tree hashing.

Expected common semantics include:

- four record slots total (three ruled + one fallback);
- two worksheet nodes;
- `source_file` values `Alpha/Ruled.pdf` and `Zeta/Fallback.pdf`;
- `source_page=1` for all records;
- repaired `headword=ġzr wrapped` on the ruled rows;
- `cuc_tablet=KTU 1.14`, `KTU 1.15`, and `KTU 1.16` on canonical rows;
- `conversion-report.json` source format `pdf`, identical source tree hash/file count, graph/check status `ok`;
- normal worksheet/section/entry navigation from the common graph builder.

The fixture strings are invented for testing and should remain explicitly labelled synthetic in comments/research documentation.

## Determinism boundary

Evidence is valid only inside the exact resolved execution environment recorded by CI. Real PDF extraction depends on `pdfplumber`, `pdfminer.six`, font metrics/substitution behavior, Python, and platform.

The comparator from #7 should be reused unchanged. Therefore the PDF replay inherits its fail-closed surface:

- exact generated `.tf` filename set;
- only exact `@dateWritten=` lines excluded, required once per TF file;
- all other persisted TF/config/metadata/body content compared;
- full conversion report compared with no ignored fields;
- independent `loadAll()` plus complete nodes/node features/edge targets+values/navigation comparison.

No PDF-specific volatility exclusion is justified by research. If repeated real parsing produces another difference, the test must fail and trigger investigation rather than widening the whitelist.

## TDD gate

This is an evidence-harness ticket with no identified production nondeterminism defect. Preserve an explicit RED without manufacturing scholarly converter behavior:

1. add the deterministic standard-library PDF generator and the repeated real PDF materialization test;
2. run both real PDF conversions and the existing complete semantic comparator in the RED test;
3. after those steps, call a deliberately not-yet-implemented test-harness contract assertion for the expected real-parser semantics;
4. commit/run that exact head and require failure specifically at the missing fixture-contract helper;
5. GREEN adds only the test-harness assertion helper unless the replay itself exposes a real converter defect.

This preserves research → plan → RED → GREEN history while ensuring RED already proves the synthetic PDFs are parseable and both real materializer executions are reached. The missing helper is an evidence-contract seam, not an invented production bug.

## Environment evidence

No new workflow machinery is needed: the merged #7 workflow records the execution environment in every supported Python test job after `pip install .` and before the suite. The successful #6 exact-head jobs will therefore contain the relevant PDF dependency closure as part of the sorted installed distribution set.

## Scope and licensing conclusion

A programmatically generated PDF using original test strings and standard PDF syntax is suitable for this evidence slice. No Burns source bytes, text, scans, screenshots, table data, or derivative artifacts are needed or permitted. Generated PDFs remain ephemeral temporary test inputs and are not uploaded as CI artifacts.
