# Research: Burns Agora status after parent-resource support was deferred (#47)

## Current state

The Burns repository now has two intentionally different product surfaces:

1. **Local / Context-Fabric product:** the reviewed CUC-aligned Burns feature module is complete. The public `ugarit-context-parsing module ... --cuc ...` CLI is the primary local producer, and exact integration CI proves CUC + Burns through Context-Fabric/cfabric-mcp.
2. **Agora registration:** `agora.materializer.json` still contains the two legacy one-source standalone materializers because current supported Agora cannot truthfully supply both the user-local Burns source and a separately trusted exact CUC parent path.

This distinction is correct. The README status prose is not.

## Upstream status evidence

`alexsosn/Agora#135` (`Support parent-resource inputs for feature-module materializers`) is now closed with state reason `not_planned` (closed 2026-09-10). Its implementation PR #141 was also closed unmerged. The capability was removed from the immediate Agora 1.0 scope rather than completed.

Therefore the README statements that the capability "is tracked in `alexsosn/Agora#135`" and especially "Until that lands" read as an active/pending implementation dependency and are stale.

## Burns migration evidence

Burns #29 remains the product/Agora migration tracker. Its branch/PR #45 preserved a clean tests-only RED for the intended product shape:

- new primary `burns-workbooks-{csv,pdf}-cuc-module` IDs;
- `module {source} --cuc {parent} --output {output}` execution;
- feature-module output composition over exact CUC 0.2.8;
- old standalone IDs retained as deprecated compatibility paths.

That RED failed only because production still exposes the legacy manifest. Existing Agora and Context-Fabric contracts remained green. PR #45 was closed unmerged once Agora #135 became `not_planned`; its branch remains evidence for a future policy/capability change.

## Repository audit

The stale product-state wording is in README's `### Agora status` section. Other primary module/CLI documentation is already truthful:

- README leads with `module` as the primary product;
- `convert` is explicitly deprecated;
- no fake one-input module is advertised;
- current `agora.materializer.json` truthfully exposes only the legacy single-input materializers.

No converter, manifest, version, license, normalization, alignment, or generated-data change is needed for #47.

## Correct wording contract

The README should say, in substance:

- current Agora registration remains the two legacy one-source materializers;
- the CUC-aligned Burns module is nevertheless complete and usable locally / through Context-Fabric;
- parent-aware Agora materializer execution is **deferred / unavailable in current supported Agora scope**, not merely pending;
- Agora #135 is the closed/deferred prerequisite and Burns #29 remains the migration tracker;
- if Agora restores a parent-resource contract, #29's preserved research/plan/RED should be resumed rather than inventing a one-input workaround;
- Burns will not copy CUC into its source/output, enable implicit network acquisition, or mislabel a standalone corpus as a feature module to bypass the limitation.

## Test strategy

Use a narrow static documentation contract over the `### Agora status` section. The test should extract that section and assert stable semantic markers rather than the whole paragraph byte-for-byte.

Required concepts:

- `legacy` and `one-source`/`single-input` current registration;
- `deferred` (or equivalent explicit current-scope block);
- references to `Agora#135` and Burns `#29`;
- working public `module` CLI path;
- no fake one-input workaround.

Forbidden stale wording:

- exact phrase `Until that lands`;
- wording that says #135 is merely tracked/pending as though it were open.

This contract is deliberately documentation-only and must not force a manifest or runtime change.
