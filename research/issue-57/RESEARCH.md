# Issue 57 research: conversion-report producer/version semantics

## Observed drift

The frozen first-release candidate advertises `0.3.0` in both installed package metadata and `agora.materializer.json`, but the deprecated standalone `conversion-report.json` still hard-codes:

```json
"converter": {"name": "ugarit-context-parsing", "version": "0.2.0"}
```

That value is producer provenance, not report-format compatibility. New 0.3.0 conversions therefore currently claim they were produced by 0.2.0.

## Separate identities

Two independent version concepts already exist and should remain independent:

1. `schema_version == 1` identifies the structure/meaning of `conversion-report.json`.
2. `converter.version` identifies the software release that produced one report.

Changing the package release without changing report structure must update only `converter.version`; changing report schema in the future must be a deliberate `schema_version` migration and does not imply a package-major/minor mapping.

## Do not use producer version for legacy artifact ownership

Issue #54 correctly treats old valid Burns reports as owned based on stable converter identity/schema/status, not an exact producer version. A genuine artifact produced by 0.2.0 must remain replaceable by a later supported converter. #57 must not tighten ownership to the current package version.

## Source of producer version

Do not introduce a second hard-coded Python version constant. The authoritative release version is installed distribution metadata produced from `pyproject.toml` by Hatchling and already verified by the release contract.

Use `importlib.metadata.version("ugarit-context-parsing")` when building a report. This gives the actual installed distribution version and automatically follows future package releases without another manual edit in `report.py`.

The supported public CLI is an installed package entry point (`ugarit-context-parsing`). CI already installs the package before executing tests. Library-level source-tree calls without installed distribution metadata are not a reason to invent a fallback version: silently reporting `unknown` or parsing `pyproject.toml` at runtime would create weaker provenance and packaging coupling. If distribution metadata is unavailable, producer provenance should fail explicitly rather than lie.

For focused unit tests, mock the metadata lookup where a synthetic producer version is useful; integration tests should exercise the installed package and require `converter.version == importlib.metadata.version("ugarit-context-parsing")`.

## Determinism

Distribution version is stable for a given installed producer and contains no machine path, timestamp, or mutable environment data. It therefore preserves existing report determinism within one release/environment identity. Reports from two different releases are expected to differ in producer provenance.

## Compatibility with current ownership safety branches

#54/#55 are stacked post-release safety work and inspect report ownership. Their ownership contract must continue to accept old producer versions. #57 should be implemented independently from frozen `master`; after `v0.3.0` publication, post-release branches may be rebased/ordered as needed before merge.

## Scope

Change only producer-version provenance and tests/documented semantics. Do not change:

- `schema_version`;
- report fields/counts/checks apart from `converter.version`;
- package or manifest version;
- legacy artifact ownership rules;
- graph/module/alignment/CUC behavior;
- the frozen `v0.3.0` release candidate.

This is post-release maintenance and must not merge before GitHub Release `v0.3.0` exists at exact commit `4994a45c53a73c09a4939731bc56af585b3ba30a`.
