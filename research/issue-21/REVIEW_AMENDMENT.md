# Review amendment: child-ticket boundaries for #21

A pre-final adversarial pass found one inconsistency between the initial research/plan wording and the safer implementation decomposition created after those documents were committed.

## Finding

The initial `RESEARCH.md` implementation-slicing list and `PLAN.md` child-ticket strategy bundled Context-Fabric combined-consumer work with standalone-materializer deprecation. That couples an external consumer seam to a user-facing migration decision and could encourage deprecating the working legacy path before the replacement consumer path is proven.

## Corrected authoritative dependency graph

The created child tickets supersede that bundled wording:

1. #22 — normalized Burns annotations + stable source IDs;
2. #23 — conservative Burns-reference grammar + fingerprinted CUC 0.2.8 index;
3. #26 — Burns→CUC alignment engine + complete disposition/accounting report;
4. #27 — feature-only Burns TF module writer + combined CUC Text-Fabric load;
5. #28 — real Context-Fabric/cfabric-mcp combined-consumer contract, with CUC and Burns module kept separate;
6. #29 — only after #28 is green, migrate/deprecate the provisional standalone product path and update downstream Agora composition/registration.

#23 follows #22; #26 follows #22/#23; #27 follows #26; #28 follows #27; #29 follows #28. Parent #21 remains open across the full chain.

## Safety consequence

Legacy standalone materializers remain unchanged through #28. A consumer limitation discovered in #28 must be preserved and tracked at the consumer seam; it must not be hidden by copying CUC into Burns output, nor used as a reason to deprecate the working legacy path prematurely.

This amendment changes planning only. No production code, source parser, TF artifact, manifest, or consumer behavior is modified by the parent research PR.
