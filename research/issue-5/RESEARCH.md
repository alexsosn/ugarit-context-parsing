# Research: completeness of Burns CSV determinism evidence (#5)

## Question

What evidence is still missing before Agora may treat the Burns CSV materializer as semantically deterministic for one exact verified runtime environment?

## Current baseline

Revalidated against `master@f271e5697a2dc5c13c783338e2a603ab5434678b`, which merged PR #4 / issue #3 after the original #5 research began.

Current `tests/test_text_fabric_integration.py` now already contains a real repeated-run CSV determinism test. It:

- creates two synthetic source roots with identical relative files/bytes but opposite creation order;
- executes the real CLI twice into fresh output directories;
- proves source bytes remain unchanged;
- compares every emitted `.tf` file byte-for-byte after removing only Text-Fabric's generated `@dateWritten=` line;
- compares complete `conversion-report.json` objects;
- independently reloads both outputs with real `Fabric(...).loadAll()`;
- compares `Fall()` and `Eall()` inventories, every node feature value across the full node range, node types, and section/navigation structure.

That is strong evidence and supersedes the earlier statement that integration coverage was one-shot. #5 is therefore a completeness-hardening ticket, not a request to invent replay from scratch.

## Findings

### 1. Current replay already establishes source-root and filesystem-creation-order independence

The merged #4 test deliberately creates identical CSV trees in different absolute roots and opposite file-creation order. Both runs resolve to identical source snapshots and generated scholarly output. This directly exercises the sorted CSV discovery contract and proves absolute source-root spelling does not enter converter output.

No additional duplicate replay test is needed merely to establish that property.

### 2. Complete normalized persisted bytes are a strong backstop, but not the semantic API contract

The existing comparison of all `.tf` files after removing only `@dateWritten=` is stricter than a semantic comparison within the currently resolved Text-Fabric runtime. It catches any persisted body/header difference that survives the one explicit generated timestamp exclusion.

However, Agora's reusable-cache policy is intentionally defined in terms of semantic/content determinism inside an exact verified runtime environment. The replay should therefore also express the complete loaded semantic state explicitly rather than relying on serializer bytes as the only exhaustive backstop.

The normalized byte comparison should stay. #5 adds semantic completeness; it should not weaken the existing test or broaden the normalization whitelist.

### 3. Node-feature coverage is already complete

The current test dynamically enumerates `Fall()` and compares every feature value for every node in the full node range. This covers `otype`, source provenance, domain features, generated hierarchy labels, CUC identifiers, and future node features without a hard-coded allowlist.

No separate node-feature comparator is missing.

### 4. Edge-feature *inventory* is compared, but edge mappings/values are not

The current test asserts `tuple(api_a.Eall()) == tuple(api_b.Eall())`, but it does not compare `Es(feature).items()` for each edge feature.

Today the converter emits `oslots`, and the exhaustive normalized `.tf` byte comparison catches drift in that file. But a semantic replay contract should directly compare every loaded edge mapping and retain values if valued edge features are introduced later.

This is the main semantic-completeness gap.

### 5. Feature metadata is not explicitly compared through the loaded API

Persisted `.tf` equality currently catches metadata differences except `@dateWritten`, but the loaded semantic snapshot does not record `Fs(feature).meta` / `Es(feature).meta`.

Content-bearing metadata such as dataset/source/license/feature descriptions/value types is part of the emitted contract and should be represented in the semantic snapshot. Text-Fabric-generated `dateWritten` is the one known volatile metadata field and must be excluded explicitly, matching the existing persisted normalization. No blanket metadata ignore is justified.

### 6. The current comparator has no negative control

The merged replay proves two real outputs compare equal, but it does not prove a reusable semantic-normalization helper would detect a meaningful mutation.

A test-only semantic snapshot should have negative controls that mutate copied normalized state and prove inequality for at least:

- a node-feature value;
- an edge mapping/value;
- a conversion-report field.

These controls should not modify converter production code or generated source fixtures.

### 7. Current fixture does not exercise duplicate generated `~N` hierarchy labels

The existing fixture exercises multiple worksheets, sections, entries, Unicode values, KTU normalization, and creation-order independence, but its repeated section/entry labels do not force `_occurrence_label()` to generate a `~2` suffix.

Because duplicate-label counters are deterministic state, the evidence fixture should include a non-contiguous repeated section/entry label and assert the expected suffixed hierarchy label. This is a test-fixture hardening change only.

### 8. Environment identity is still missing from the evidence log

`pyproject.toml` intentionally permits dependency ranges such as `text-fabric>=13.1,<14` and `pdfplumber>=0.11`. The same converter commit can therefore run under different resolved dependency/runtime closures.

The ordinary CI matrix identifies Python versions, but the replay itself does not emit a canonical record of the actual platform and resolved installed distributions used for the evidence run.

#5 should print one deterministic `DETERMINISM_ENVIRONMENT=<json>` record containing Python implementation/version, OS/platform/machine, and sorted installed distribution names/versions. No generated TF artifact should be uploaded.

This upstream evidence still does **not** authorize Agora reuse by itself. Agora must independently replay/verify inside the exact managed installation and bind reusable policy to its integrity-verified `execution_identity_sha256`.

### 9. PDF remains a separate evidence problem

Nothing in merged #4 or this hardening ticket proves the PDF materializer deterministic. Real PDF extraction depends on the packaged pdfplumber-based parser and resolved runtime behavior.

PDF must remain unknown/non-reusable until an equivalent legal synthetic-PDF replay exercises the real parser twice.

## Revised evidence boundary

### Already proven by merged #4

- two real CSV CLI executions;
- distinct absolute source/output roots;
- opposite source-file creation order;
- source immutability;
- normalized equality of every generated `.tf` file modulo only `@dateWritten`;
- complete conversion-report equality;
- complete dynamic node-feature equality;
- feature-inventory equality;
- section/navigation equality;
- real Text-Fabric save/reload.

### Still required by #5

- dynamic equality of every loaded edge feature mapping/value;
- loaded feature metadata equality excluding only generated `dateWritten`;
- negative controls proving semantic-snapshot sensitivity;
- duplicate generated-label fixture coverage;
- canonical environment evidence in CI logs.

## TDD implication

The RED should extend the existing merged replay rather than duplicate it. Add an intentionally unimplemented test-only semantic-snapshot seam that is invoked **after** both real conversions and the existing persisted/API assertions succeed. The first #5 RED must fail with `NotImplementedError` at that seam.

GREEN should implement only the test harness/snapshot and fixture/evidence additions unless a genuine converter semantic delta is discovered. If repeated outputs differ semantically, stop and create a focused converter RED before any production change.

## Scope boundary

This ticket strengthens evidence for the existing CSV converter. It does not alter Agora cache behavior, change scholarly normalization, redistribute Burns-derived data, weaken the existing normalized-byte check, or imply PDF determinism.
