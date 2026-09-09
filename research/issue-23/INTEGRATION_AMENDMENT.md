# Integration and adversarial evidence amendment (#23)

This amendment records failures found after the initial RED/GREEN unit cycle. They are retained because each exposed an assumption that synthetic fixtures alone did not exercise.

## Preserved primary RED

Head `c1f983589531667c77b436d88da9e7b0416ea87b`, standard run `34358575840`.

All Python jobs reached the new test modules and failed at the planned missing-production seams (`ugarit_context_parsing.references` / `ugarit_context_parsing.cuc_index`). Existing repository provenance/consumer gates remained healthy. Production implementation followed only after that RED was attested.

## Core synthetic GREEN

Head `3f03d89694290dfbcb3833956846a0a1b0303541`, standard run `34358963225`.

The conservative reference parser and pure CUC snapshot/index builder passed Python 3.10/3.12/3.13 plus existing compatibility gates before a real-CUC public-path workflow was added.

## Real-CUC integration failure 1: relative Text-Fabric location

Permanent integration workflow first exercised the public builder against the exact reviewed CUC checkout in run `34359079385`.

The six required-file fingerprint verification succeeded. Text-Fabric then interpreted the relative `.cuc/tf/0.2.8` location incorrectly and failed to load the corpus.

Correction: preserve verification against the caller-supplied path first, then resolve that already-validated directory to an absolute path before handing it to `Fabric`. This keeps the fingerprint/symlink gate authoritative while using Text-Fabric's expected location form.

## Real-CUC integration failure 2: section metadata API assumption

After the path correction, run `34359600980` reached and loaded the exact CUC Text-Fabric base, then failed semantic verification because the implementation assumed `T.sectionFeatures` was the tuple of configured feature names. Under Text-Fabric 13.1 it exposes loaded feature-value maps instead.

Correction: read the authoritative `@sectionTypes` / `@sectionFeatures` names from the real non-symlink `otext.tf`, while Text-Fabric remains responsible for structural/node extraction. The pure builder still compares those values to the reviewed `tablet,column,line` contract.

The corrected public path subsequently passed exact-CUC integration in run `34359867285`.

## Independent adversarial RED: mutable expectations and real CUC whitespace

After the public integration succeeded, an independent challenge found two additional issues and preserved them as tests on head `39e3a47179743a584fa7021deb2998d65c829807`, standard run `34360085103`:

1. `REVIEWED_CUC_COUNTS` was an exported mutable dictionary used by public semantic verification. The adversarial test requires a read-only mapping.
2. The reviewed CUC contains incidental surrounding whitespace in at least one column value. Burns reference parsing produces canonical Roman column names, so raw whitespace-bearing CUC keys would be unreachable. Tests require column-key whitespace normalization and require collisions introduced by normalization to fail closed.

The run failed only these new checks while the established Burns/reference/materialization tests remained green.

Correction: expose reviewed counts through `MappingProxyType`; strip only surrounding CUC column-key whitespace in the index layer; reject empty normalized column names; and perform duplicate-column/exact-line checks after the same canonicalization.

The permanent exact-CUC integration workflow now additionally asserts that all exported column and exact-line keys are whitespace-canonical while retaining the reviewed cardinalities. This proves the behavior against the real fingerprinted corpus, not only synthetic snapshots.

## Scope remains unchanged

These corrections do not perform Burns→CUC alignment, headword matching, module writing, consumer composition, or legacy deprecation. They harden only the #23 syntax/base-index foundation used by later #26 alignment work.

No Burns-derived rows/references/headwords/comments and no CUC corpus payload are committed by this evidence.