# Issue 52 research: reviewed-CUC local quickstart

## Current user path

Reviewed base: `4994a45c53a73c09a4939731bc56af585b3ba30a` (the frozen v0.3.0 release candidate).

README already documents:

- Python 3.10+ installation from a repository checkout with `python -m pip install .`;
- the primary `ugarit-context-parsing module` CLI;
- CSV and PDF module commands;
- the exact reviewed CUC identity `DT-UCPH/cuc@ad69400f5446e1c8217af01659c7c10ab00c015b`;
- Text-Fabric path/version `tf/0.2.8`;
- that the converter does not download CUC automatically;
- the current Agora limitation.

The usability gap is that examples still use `/path/to/cuc/tf/0.2.8`, so a new user must infer how to acquire the exact parent tree safely.

## CUC identity

The reviewed commit exists upstream and is immutable:

- repository: `https://github.com/DT-UCPH/cuc.git`;
- commit: `ad69400f5446e1c8217af01659c7c10ab00c015b`;
- TF directory passed to Burns: `cuc/tf/0.2.8` after checkout.

Burns independently validates the reviewed required CUC files by exact size/SHA-256 and validates the expected Text-Fabric structure/counts before alignment. Acquisition therefore does not become a new trust bypass: an incorrect/incomplete checkout fails before module publication.

## Acquisition options considered

### Full clone + checkout

`git clone` followed by `git checkout --detach <sha>` is easy to understand but downloads unnecessary repository history.

### Archive URL

A GitHub commit archive avoids history, but introduces `curl`/archive extraction and a SHA-derived directory name. It is less uniform with ordinary Git-based developer workflows.

### Minimal Git fetch — selected

Use an empty local repository, add the canonical upstream remote, fetch only the exact reviewed commit at depth 1, then detached-checkout `FETCH_HEAD`:

```bash
git init cuc
git -C cuc remote add origin https://github.com/DT-UCPH/cuc.git
git -C cuc fetch --depth 1 origin ad69400f5446e1c8217af01659c7c10ab00c015b
git -C cuc checkout --detach FETCH_HEAD
```

Properties:

- explicitly names the immutable reviewed commit;
- avoids silently following upstream `main`;
- avoids downloading unrelated history;
- keeps network acquisition visibly outside the converter;
- leaves a normal Git worktree whose commit can be inspected locally;
- produces the stable path `cuc/tf/0.2.8` used by the module command.

## Installation boundary

This issue does not change packaging or claim a release that does not yet exist. The quickstart can use `python -m pip install .` from a repository checkout. Once `v0.3.0` is actually published, a later documentation edit may additionally show a tag-pinned Git install, but this issue must not fabricate that publication state.

## Data/license and Agora boundaries

- CUC acquisition is separate from Burns source acquisition; neither is bundled with this repository.
- CUC retains its upstream license.
- Burns Workbooks remain under CC BY-NC-ND 2.5 and generated Burns-derived artifacts remain user-local.
- The quickstart must not imply Agora can currently acquire/bind CUC for the parent-aware module. Current Agora registration remains the two legacy one-source materializers.

## Merge ordering

Prepare and review this documentation change independently, but do not merge it before the frozen `v0.3.0` release candidate is actually published. This avoids moving `master` while the first release still needs to be created at exact SHA `4994a45c53a73c09a4939731bc56af585b3ba30a`.