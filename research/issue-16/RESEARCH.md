# Issue 16 research: first stable release

## Current state

Reviewed base for this release slice: `237be081f2ba0ff17443aafebd09bbb1a4fa7a93`.

At that commit:

- package version in `pyproject.toml`: `0.2.0`;
- plugin version in `agora.materializer.json`: `0.2.0`;
- repository Git tag refs: none;
- repository GitHub Releases: none;
- repository software license: MIT, with PEP 639 package metadata;
- the public CUC-aligned `module` CLI is complete and tested;
- legacy `convert` remains available with an explicit deprecation diagnostic;
- README truthfully states that current Agora registration remains the legacy one-source materializers and parent-aware module registration is deferred.

Agora currently registers this plugin at commit `e1218b88d9d849c58ee25541339f32b0d8f5a7d3`, version `0.2.0`, with release tracking disabled and stale `software: NOASSERTION` metadata.

## Version decision

Use **0.3.0** / tag **`v0.3.0`**.

Earlier preliminary #16 research suggested 0.2.1 when the changes after the original Agora pin were only hardening/evidence. That conclusion is now obsolete: since then the repository has added a new supported public product surface, the CUC-aligned feature-module CLI, while retaining the old standalone converter for compatibility.

This is a backward-compatible feature addition rather than a breaking removal, so the next minor version is appropriate. Reusing `0.2.0` is also inappropriate because that version is already advertised by package metadata, the materializer manifest and Agora's registry even though no GitHub release/tag was ever created.

## Release identity contract

The release identity must align all upstream version-bearing surfaces:

- `pyproject.toml` project version: `0.3.0`;
- `agora.materializer.json` `plugin.version`: `0.3.0`;
- Git tag: `v0.3.0`;
- GitHub Release: published, non-draft, non-prerelease `v0.3.0`.

No CUC version changes in this release. Burns modules remain bound to reviewed CUC `0.2.8` at commit `ad69400f5446e1c8217af01659c7c10ab00c015b` through the exact compatibility fingerprint.

## Release scope

User-visible release contents:

1. **CUC-aligned Burns feature module** as the primary local product:
   - `ugarit-context-parsing module ... --cuc ...`;
   - feature-only output, no Burns warp;
   - conservative tablet/line/word/span alignment with explicit unresolved/ambiguous/out-of-CUC accounting;
   - lossless overlapping/multi-valued Burns annotations;
   - exact reviewed-CUC compatibility fingerprint in TF metadata/report.
2. **CSV and real PDF source paths** feeding the same reviewed module pipeline.
3. **Context-Fabric/cfabric-mcp composition** with CUC and Burns as separate locations, with CUC warp/navigation unchanged.
4. **Determinism and source-integrity evidence**:
   - repeated synthetic CSV semantic determinism;
   - real-parser synthetic PDF determinism;
   - environment/dependency evidence;
   - source-root/descendant symlink rejection.
5. **Legacy standalone compatibility**:
   - `convert` remains available but is explicitly deprecated.
6. **MIT software license**, separately scoped from Burns CC BY-NC-ND 2.5 source/generated-data restrictions.

## Explicit boundaries

The release must not imply:

- that Burns-derived CSV/PDF/TF data are redistributable under MIT;
- that any Burns source/derived artifact is bundled as a release asset;
- that CUC itself is bundled or relicensed;
- that current Agora can execute the parent-aware CUC module materializer;
- that the legacy standalone Agora materializers have been removed.

GitHub's automatic source-code archives are acceptable because the repository itself contains no Burns-derived source/generated artifacts.

No PyPI publication is part of #16 unless separately requested; this ticket's publication target is the GitHub release and Agora's immutable registry/release-tracking metadata.

## Agora release-tracking contract

Agora's stable materializer release tracker accepts only published, non-draft, non-prerelease GitHub Releases tagged `v<strict SemVer>`. It resolves the tag to an immutable commit and validates the exact `agora.materializer.json` at that commit before proposing registry changes.

After the upstream release exists, update Agora's `ugarit-context-parsing` registry entry to:

- `ref`: exact `v0.3.0` release commit SHA;
- `version`: `0.3.0`;
- `release_tracking.mode`: `github-releases`;
- `release_tracking.channel`: `stable`;
- `release_tracking.tag_prefix`: `v`;
- `licenses.software`: `MIT`.

Keep the registered materializer IDs unchanged because current Agora still exposes only the legacy single-input materializers. Enabling release tracking is passive discovery/review metadata and must not pretend parent-resource execution exists.

## Release evidence

Before publication, the release-prep PR must preserve a version-alignment RED and then pass all current repository gates on one frozen head. After merge, the **exact master commit that will be tagged** must also pass its push-triggered required workflows before the release is published.

Perform an independent adversarial release review on that exact release commit, challenging version identity, data/license boundaries, release notes, manifest stability, and absence of restricted assets.
