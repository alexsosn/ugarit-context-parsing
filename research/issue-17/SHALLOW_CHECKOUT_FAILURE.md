# GREEN failure amendment: shallow checkout parent traversal (#17)

The first live GREEN attempt failed in every `Verify CI provenance` step before downstream tests ran.

## Preserved failure

Candidate head `80d5afe11f92403b3392e6c238c53a4fed463a99`, run 65, checked out synthetic merge `e2e1e0d2ea261646fd095f7917ebfd1bb4c9bb5c`. The checkout log identified it as the merge of head `80d5afe11f92403b3392e6c238c53a4fed463a99` into base `3c323f6540c9b8d791be3f62b1a6fbdd505243b5`.

The provenance script then observed zero parents from `git show -s --format=%P HEAD` and failed closed with:

`pull_request merge checkout must have exactly two parents, got 0`

## Root cause

`actions/checkout` uses `fetch-depth: 1` here. Git shallow repositories mark boundary commits so revision traversal treats those commits as having no parents, even though the commit object itself still records its parent object IDs. Git's shallow documentation explicitly describes this graft behavior.

Increasing fetch depth would make traversal evidence available but would expand network/history scope in every job solely for provenance checking.

## Correction

Keep `fetch-depth: 1` unchanged and inspect the checked-out commit object directly with `git cat-file -p HEAD`. Git documents `cat-file -p` as returning the object's contents; commit object headers contain the ordered `parent <sha>` lines even when traversal is stopped by the shallow boundary.

Add a pure raw-commit parser with negative tests, then feed those ordered parent IDs into the existing fail-closed base/head validation. This preserves the intended evidence while avoiding a checkout-performance change.
