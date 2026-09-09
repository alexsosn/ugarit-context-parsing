# Research: upgrade GitHub Actions runtime references (#14)

## Question

Which current `actions/checkout` and `actions/setup-python` releases should this repository use, how should they be pinned, and can the upgrade be made without changing CI semantics?

## Baseline

Repository baseline: `master@c6f165a3ebf8c9ed3ef0bd2dc2a7bbc8090ed219`.

The current workflow uses Node-20-era action majors and GitHub-hosted runners emit deprecation warnings while forcibly executing them on Node 24. The workflow now contains the ordinary Python matrix, the pinned Agora manifest contract, and the pinned Context-Fabric/cfabric-mcp consumer contract.

## Reviewed upstream releases

### actions/checkout

Reviewed stable release: `actions/checkout` v7.0.1.

The tag resolves to immutable commit:

`3d3c42e5aac5ba805825da76410c181273ba90b1`

Relevant v7 behavior:

- v5 moved the action runtime to Node 24 and requires Actions Runner >=2.327.1;
- v6 changed persisted checkout credentials to a separate file under `$RUNNER_TEMP`, while normal authenticated Git operations remain supported;
- v7 migrated internals to ESM and updated dependencies/security fixes;
- v7 refuses unsafe fork-PR checkout by default for `pull_request_target` and `workflow_run`; this repository uses ordinary `pull_request`, so the new safety check does not alter the current trigger path;
- repository/ref/path inputs remain supported, including the nested pinned Agora and Context-Fabric public-repository checkouts;
- default checkout still fetches one triggering ref/SHA unless configured otherwise.

The v7.0.1 release additionally contains fixes around the unsafe-PR check, branch whitespace handling, and escaping values passed to `git config --unset`.

### actions/setup-python

Reviewed stable release: `actions/setup-python` v7.0.0.

The tag resolves to immutable commit:

`5fda3b95a4ea91299a34e894583c3862153e4b97`

Relevant behavior:

- v6 moved the action runtime from Node 20 to Node 24 and requires Actions Runner >=2.327.1;
- v7 migrated internals to ESM and documents no changes to action inputs, outputs, or behavior;
- `python-version` remains supported;
- `cache: pip` remains supported and still hashes normal dependency metadata such as `pyproject.toml`;
- the removed legacy `pip-install` input is not used by this repository.

The currently observed GitHub-hosted runner version is newer than the minimum required by both actions.

## Workflow inventory

`.github/workflows/test.yml` contains all relevant action uses:

| Job | checkout uses | setup-python uses | Relevant inputs |
| --- | ---: | ---: | --- |
| `test` | 1 | 1 | matrix `python-version`; `cache: pip` |
| `agora-contract` | 2 | 1 | nested `repository`, exact `ref`, `path`; Python 3.13 |
| `context-fabric-contract` | 2 | 1 | nested `repository`, exact `ref`, `path`; Python 3.13; `cache: pip` |
| **Total** | **5** | **3** | |

No other workflow file is in scope for these two actions at the baseline.

## Pinning decision

Use immutable full commit SHAs for every action reference, with a trailing human-readable release comment:

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`

Rationale:

1. A moving `@v7` reference can resolve to different action source without a repository diff.
2. The repository already pins downstream Agora and Context-Fabric source revisions exactly for reviewable compatibility evidence.
3. Full action SHAs make the executed dependency source auditable and preserve a deterministic review target.
4. Version comments keep maintenance readable without weakening the pin.

The cost is that action patch updates become explicit maintenance changes. For this small workflow, reviewable source identity is preferable to silent floating updates.

## Intended semantic delta

The implementation should change only the eight `uses:` references. It must not alter:

- triggers or permissions;
- Python 3.10/3.12/3.13 matrix coverage;
- pip cache configuration;
- Agora or Context-Fabric repository/revision/path inputs;
- environment evidence;
- installed-package verification;
- contract commands.

## TDD/evidence gate

Before the workflow is modified, add an offline unit test that reads `.github/workflows/test.yml`, extracts only `uses:` references for `actions/checkout` and `actions/setup-python`, and requires:

- exactly five checkout references, all at the reviewed v7.0.1 immutable SHA;
- exactly three setup-python references, all at the reviewed v7.0.0 immutable SHA;
- no moving major tags or obsolete action refs for these two actions.

The test must not access the network or parse unrelated workflow semantics. On the unchanged baseline it should fail because all eight references still point to `checkout@v4` / `setup-python@v5`.

## Acceptance evidence after GREEN

After replacing only the action references:

- the workflow-reference contract passes;
- ordinary tests remain green on Python 3.10, 3.12 and 3.13;
- environment evidence and installed-package checks still run;
- Agora contract remains green;
- Context-Fabric consumer contract remains green;
- job logs no longer report Node 20 deprecation attributable to checkout/setup-python;
- the final diff receives a logically independent adversarial review before merge.

## Scope boundary

Issue #17 separately covers the distinction between literal PR-head CI and GitHub's synthetic merge-ref checkout semantics. This ticket must not change that provenance model while upgrading action runtimes.
