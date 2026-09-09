# Plan: feature-only Burns TF module and combined CUC load (#27)

## Gate 1 — representation RED

Add tests against a missing `ugarit_context_parsing.module_writer` production seam. Synthetic annotations/alignment only; no Burns source wording.

Require:

- module data contains no warp features and references existing CUC node IDs only;
- authoritative `burns_annotations` is canonical JSON and preserves two occurrences on one node;
- a multi-word occurrence is replicated to each carrier but embeds the same full ordered span and reconstructs once by `(occurrence_id, anchor_nodes)`;
- nested/overlapping spans coexist;
- repeated identical occurrence input cannot create duplicate entries;
- ordering is deterministic under shuffled input;
- Unicode, punctuation, and embedded newline survive JSON encode/decode.

Commit and preserve the failing run before implementation.

## Gate 2 — writer RED/GREEN

Extend RED for publication:

- `Fabric.save` receives Burns node features only;
- staged output must not contain `otype.tf` or `oslots.tf`;
- copied CUC diplomatic features are rejected from the Burns module feature inventory;
- exact reviewed-CUC metadata is present;
- failed save or publication leaves prior module/report untouched;
- successful publication replaces stale Burns `.tf` files and report atomically.

Implement a dedicated module writer rather than weakening standalone `writer.py` invariants. Share only small transactional helpers if that reduces duplication without changing standalone behavior.

## Gate 3 — combined Text-Fabric integration

Create a permanent integration workflow/test using the exact reviewed CUC commit, analogous to the existing pinned downstream contracts. It must load base CUC and a synthetic Burns module together and assert unchanged warp/type counts plus exact payload round-trip.

The integration fixture must contain no Burns-derived source data. If Text-Fabric module loading exposes a different supported location/module arrangement than assumed in research, amend research/plan before adapting production code; do not copy CUC into module output.

## Gate 4 — report integrity

The publication report must be derived from the same alignment objects as the module payload and retain complete accounting for annotations with no carrier node. Reject caller-forged payload/report combinations where practical; at minimum test that report annotation/occurrence counts and IDs correspond to the provided alignments.

## Gate 5 — full tests and cleanup

Run Python 3.10/3.12/3.13, installed-package checks, standalone materializer tests, Agora contract, Context-Fabric contract, and the new reviewed-CUC module integration. No temporary research workflow may remain.

## Gate 6 — independent adversarial review

Freeze one exact head. Review independently for:

- accidental `otype`/`oslots` or copied CUC feature output;
- carrier-node replication being mistaken for occurrence multiplicity;
- overwrite/loss under overlapping annotations;
- unstable JSON/order;
- metadata insufficient to reject incompatible CUC bases;
- partial publication/rollback failures;
- convenience features diverging from authoritative JSON;
- real Burns-derived payload in tests/artifacts;
- changes to legacy standalone behavior before #28/#29.

Only after exact-head CI and no blocking findings: mark ready and merge guarded by `expected_head_sha`.

## Definition of done

A user can generate a Burns feature-only TF module whose annotations attach to the reviewed CUC node universe without duplicating the Ugaritic corpus. Direct Text-Fabric loading of CUC + Burns preserves the CUC warp exactly and exposes lossless Burns multiplicity/spans. Context-Fabric and product migration remain separate downstream gates.