# Plan: repeated semantic determinism evidence for Burns CSV (#3)

## Goal

Add one reproducible synthetic integration test proving that two fresh Burns CSV -> Text-Fabric materializations under the same converter/dependency/runtime identity preserve identical scholarly content, while excluding only Text-Fabric's generated `@dateWritten` header from byte-level comparison.

No converter production behavior should change unless the evidence test discovers a real nondeterminism defect.

## Preconditions

- Research: `research/issue-3/RESEARCH.md`.
- Baseline converter: `master@e1218b88d9d849c58ee25541339f32b0d8f5a7d3`.
- Existing real Text-Fabric integration test remains the base fixture style.
- Scope is CSV only; PDF is explicitly not inferred.

## Evidence-test slice

### Test fixture

Extend `tests/test_text_fabric_integration.py` with local helpers only as necessary.

Create one temporary CSV source tree with at least two category/worksheet files and several rows covering:

- Unicode transliteration;
- more than one worksheet/section/entry;
- canonical KTU normalization;
- deterministic file-order traversal independent of creation order.

Create files in an order intentionally different from lexical relative-path order so the test actually exercises `load_csv_directory()` sorting rather than merely agreeing with creation order.

### First materialization

1. Compute a byte-level digest/snapshot of the source tree.
2. Run the real `cli.main(["convert", ... "--input-format", "csv", ...])` into fresh output A.
3. Require success and all required TF/report files.

### Second materialization

1. Run the same real command against the same unchanged source into a separate fresh output B.
2. Require success.
3. Recompute the source snapshot and assert exact equality with the pre-run source bytes.

### Complete persisted-artifact comparison

- Assert the exact same `*.tf` filename set in A and B.
- For every `.tf` file, normalize by removing **only** lines beginning `@dateWritten=` and assert all remaining UTF-8 text is exactly equal.
- Assert both outputs actually contained `@dateWritten=` so the volatile exclusion is exercised rather than dead code.
- Compare `conversion-report.json` as complete parsed JSON objects with no excluded fields.

Do not ignore `writtenBy`, version, source metadata, ordering, whitespace, feature metadata, or any body lines.

### Independent Text-Fabric reload comparison

Load A and B independently using real Text-Fabric `Fabric(...).loadAll()`.

Assert:

- both APIs load successfully;
- `Fall()` inventories are identical;
- `Eall()` inventories are identical;
- all node types are identical for the complete node range;
- section/navigation tuples are identical for every non-slot structural node;
- expected record/worksheet/section/entry structure from the synthetic fixture is present.

The complete normalized `.tf` equality is the exhaustive persisted semantic comparison; these API assertions additionally prove loader/navigation usability.

## Gate interpretation

This is an evidence ticket, not a known bug fix. Research found no production nondeterminism beyond Text-Fabric's generated timestamp. Therefore the new test is allowed to pass on its first CI execution under issue #3's explicit evidence-test exception.

If it fails for any additional reason:

1. freeze the failing test commit as genuine RED evidence;
2. inspect the exact differing persisted/loaded state;
3. amend research/plan if the difference is legitimate volatility;
4. otherwise make the smallest production fix;
5. rerun all gates and perform a fresh independent review.

Never broaden the normalization whitelist merely to make the test pass.

## CI gates

Require the repository's full Python matrix (3.10, 3.12, 3.13) at the exact candidate head. The existing workflow also exercises Agora manifest compatibility; keep that gate unchanged.

If the evidence test is platform/runtime-sensitive, that is itself a blocker for downstream reusable cacheability until investigated. Agora's cache execution identity includes runtime/platform/dependency identity, but the upstream test must still be stable within each supported matrix cell.

## Independent adversarial review

Freeze the exact candidate SHA and review the patch without relying on the implementation rationale. Challenge at least:

- whether any scholarly/content field is excluded besides `@dateWritten`;
- whether normalized file comparison covers every generated `.tf` file;
- whether creation order really differs from lexical traversal order;
- whether source bytes are proved unchanged;
- whether both outputs are independently loaded rather than reusing one API/cache;
- whether navigation coverage includes every generated structural node;
- whether the test accidentally proves only CSV adapter behavior rather than the real writer;
- whether PDF determinism is accidentally implied;
- whether the test target is stable enough for Agora exact-commit evidence metadata.

Any blocker starts a regression/evidence sub-loop before merge.

## Definition of done

- research and plan precede the evidence test;
- repeated fresh real CSV materialization is compared exhaustively modulo only `@dateWritten`;
- complete conversion reports match;
- source input remains byte-identical;
- both outputs independently reload and expose identical full feature inventories/node/navigation structure;
- Python 3.10/3.12/3.13 exact-head CI is green;
- logically independent exact-head review finds no blocker;
- merge closes #3 and yields the immutable upstream commit Agora can review for CSV cacheability attestation.
