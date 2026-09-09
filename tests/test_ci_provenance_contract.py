from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.check_ci_provenance import validate_provenance


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
RUN_PATTERN = re.compile(
    r"^\s*run:\s*['\"]?python scripts/check_ci_provenance\.py['\"]?\s*(?:#.*)?$",
    re.MULTILINE,
)
BASE = "1" * 40
HEAD = "2" * 40
MERGE = "3" * 40
OTHER = "4" * 40


def _workflow_texts() -> list[str]:
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    return [path.read_text(encoding="utf-8") for path in paths]


def _pull_request_event() -> dict:
    return {
        "pull_request": {
            "base": {"sha": BASE},
            "head": {"sha": HEAD},
        }
    }


class CiProvenanceWorkflowContractTests(unittest.TestCase):
    def test_every_required_job_definition_invokes_provenance_checker(self):
        count = sum(len(RUN_PATTERN.findall(text)) for text in _workflow_texts())
        self.assertEqual(count, 3)


class CiProvenanceValidatorTests(unittest.TestCase):
    def test_valid_pull_request_merge(self):
        evidence = validate_provenance(
            event_name="pull_request",
            event=_pull_request_event(),
            github_sha=MERGE,
            checked_out_sha=MERGE,
            parents=(BASE, HEAD),
        )
        self.assertEqual(
            evidence,
            {
                "base_sha": BASE,
                "head_sha": HEAD,
                "mode": "pull_request_merge",
                "parents": [BASE, HEAD],
                "tested_sha": MERGE,
            },
        )

    def test_rejects_checkout_different_from_github_sha(self):
        with self.assertRaisesRegex(ValueError, "does not match GITHUB_SHA"):
            validate_provenance(
                event_name="pull_request",
                event=_pull_request_event(),
                github_sha=MERGE,
                checked_out_sha=OTHER,
                parents=(BASE, HEAD),
            )

    def test_rejects_non_merge_parent_count(self):
        with self.assertRaisesRegex(ValueError, "exactly two parents"):
            validate_provenance(
                event_name="pull_request",
                event=_pull_request_event(),
                github_sha=MERGE,
                checked_out_sha=MERGE,
                parents=(HEAD,),
            )

    def test_rejects_wrong_parent_order(self):
        with self.assertRaisesRegex(ValueError, "do not match event base/head"):
            validate_provenance(
                event_name="pull_request",
                event=_pull_request_event(),
                github_sha=MERGE,
                checked_out_sha=MERGE,
                parents=(HEAD, BASE),
            )

    def test_rejects_missing_pull_request_fields(self):
        with self.assertRaisesRegex(ValueError, "missing head/base"):
            validate_provenance(
                event_name="pull_request",
                event={"pull_request": {"head": {"sha": HEAD}}},
                github_sha=MERGE,
                checked_out_sha=MERGE,
                parents=(BASE, HEAD),
            )

    def test_valid_push(self):
        evidence = validate_provenance(
            event_name="push",
            event={},
            github_sha=HEAD,
            checked_out_sha=HEAD,
            parents=(BASE,),
        )
        self.assertEqual(evidence, {"mode": "push", "tested_sha": HEAD})

    def test_push_rejects_checkout_mismatch(self):
        with self.assertRaisesRegex(ValueError, "does not match GITHUB_SHA"):
            validate_provenance(
                event_name="push",
                event={},
                github_sha=HEAD,
                checked_out_sha=OTHER,
                parents=(BASE,),
            )

    def test_rejects_unsupported_event(self):
        with self.assertRaisesRegex(ValueError, "unsupported GitHub event"):
            validate_provenance(
                event_name="workflow_dispatch",
                event={},
                github_sha=HEAD,
                checked_out_sha=HEAD,
                parents=(BASE,),
            )


if __name__ == "__main__":
    unittest.main()
