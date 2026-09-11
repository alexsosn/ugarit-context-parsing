# Issue 15 research: software license

## Decision authority

On 2026-09-11 the repository owner explicitly selected the **MIT License** for the software/code in `ugarit-context-parsing`. This resolves the decision blocker recorded in issue #15.

The decision applies to repository software only. It does **not** alter the license of Duncan Coe Burns's thesis/Workbooks or the redistribution status of CSV/Text-Fabric artifacts derived from those sources.

## Current repository state

At the reviewed base commit `3f4537753e2429605eafd72305a865289212915e`:

- there is no repository `LICENSE` file;
- `[project]` in `pyproject.toml` has no software-license metadata;
- the README `License and attribution` section describes Burns source/data terms only;
- Agora consequently cannot infer an explicit software license from this repository.

## Code/provenance audit

Repository code search found no copyright/SPDX headers and no `adapted from` notices indicating copied source that needs a separate bundled notice. The repository does not vendor runtime dependencies; `src/`, `scripts/`, tests, research documents and project metadata are maintained in this repository, while dependencies are installed externally.

Direct runtime dependencies are compatible with an MIT-licensed application:

- Text-Fabric (`annotation/text-fabric`) is MIT licensed;
- `pdfplumber` (`jsvine/pdfplumber`) is MIT licensed;
- `cryptography` (`pyca/cryptography`, used only on the constrained macOS/x86_64 environment) is available under either Apache-2.0 or BSD terms.

These dependencies remain separately licensed external works. Selecting MIT for this project does not relicense them.

## Source/data boundary

The README already records:

- Burns thesis and Workbooks: CC BY-NC-ND 2.5;
- locally generated Workbook CSV and Burns-derived TF artifacts: derived reformatting kept local and not redistributed by this repository.

The software-license update must preserve this boundary explicitly. A reader must not be able to interpret `MIT` as applying to Burns source material or generated Burns-derived datasets.

The reviewed CUC base is also external data and is not redistributed by this repository; its own upstream license remains independent of the software license here.

## Packaging metadata

Use PEP 639-style project metadata:

```toml
[project]
license = "MIT"
license-files = ["LICENSE"]
```

With the current Hatchling build backend this should produce Core Metadata with `License-Expression: MIT` and a `License-File: LICENSE` entry. CI must prove the installed package exposes those fields rather than relying only on source-text parsing.

Do not add a version bump in this ticket; version/release alignment belongs to #16.

## License text

Add the standard MIT License text with the repository author's public commit identity:

`Copyright (c) 2026 Oleksandr (Alex) Sosnovshchenko`

No extra restrictions may be inserted into the MIT license text. Burns data restrictions belong in README/source documentation, not in the software license file.

## Required documentation shape

Rename/expand the README licensing section so it contains three unambiguous layers:

1. **Software** — repository software is MIT licensed; link to `LICENSE`.
2. **Burns source material** — source Workbooks/thesis remain CC BY-NC-ND 2.5.
3. **Generated Burns-derived artifacts** — local derived reformatting remains non-redistributed without permission.

## Test surface

Before implementation, preserve RED requiring:

- standard MIT `LICENSE` file and copyright notice;
- installed package metadata reports `License-Expression: MIT`;
- installed package metadata records `LICENSE` as a license file;
- README explicitly separates MIT software from Burns CC BY-NC-ND 2.5 source/data terms and generated-artifact restrictions.

No converter, parser, scholarly normalization, CUC compatibility, manifest version or release behavior changes belong in this ticket.
