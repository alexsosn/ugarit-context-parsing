# Review amendment: action-pin contract coverage (#14)

A pre-final adversarial review of the first GREEN implementation found two weaknesses in the offline regression contract. Neither affected the eight workflow reference changes themselves, but both could allow future CI maintenance to escape the intended guard.

## Findings

1. The original extractor matched only unquoted YAML `uses:` values. A syntactically valid quoted value such as `uses: "actions/checkout@v4"` could therefore evade the contract.
2. The original contract read only `.github/workflows/test.yml`. A newly added workflow could reintroduce an obsolete checkout/setup-python reference without being inspected.

## Amendment

Before freezing the final implementation head:

- parse only actual YAML `uses:` lines, accepting unquoted, single-quoted, and double-quoted action references plus trailing comments;
- scan every `.yml` and `.yaml` file directly under `.github/workflows/`;
- keep the exact expected inventory at five checkout and three setup-python uses, all pinned to the reviewed immutable release SHAs;
- retain a focused extractor self-test proving quoted references are detected and commented-out references are ignored.

The exact expected-count contract intentionally fails if a new workflow adds another relevant action use, even if it is correctly pinned. That forces an explicit review of the repository-wide action inventory instead of silently widening the trusted dependency surface.

This amendment changes no workflow behavior, consumer pin, Python matrix, cache configuration, or converter code. A fresh CI run after the contract hardening becomes the final candidate evidence.
