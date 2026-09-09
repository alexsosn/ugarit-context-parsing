from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.check_ci_provenance import parse_commit_parents, validate_provenance


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
TEST_WORKFLOW = WORKFLOWS / "test.yml"
RUN_PATTERN = re.compile(
    r"^\s*run:\s*['\"]?python scripts/check_ci_provenance\.py['\"]?\s*(?:#.*)?$",
    re.MULTILINE,
)
JOB_PATTERN = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
REQUIRED_JOBS = ("test", "agora-contract", "context-fabric-contract")
BASE = "1" * 40
HEAD = "2" * 40
MERGE = "3" * 40
OTHER = "4" * 40
TREE = "5" * 40


def _workflow_texts() -> list[str]:
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    return [path.read_text(encoding="utf-8") for path in paths]


def _job_blocks(workflow: str) -> dict[str, str]:
    jobs: dict[str, list[str]] = {}
    current: str | None = None
    in_jobs = False
    for line in workflow.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if line and not line.startswith(" "):
            break
        match = JOB_PATTERN.match(line)
        if match:
            current = match.group(1)
            jobs[current] = [line]
        elif current is not None:
            jobs[current].append(line)
    return {name: "\n".join(lines) for name, lines in jobs.items()}


def _pull_request_event() -> dict:
    return {
        "pull_request": {
            "base": {"sha": BASE},
            "head": {"sha": HEAD},
        }
    }


class CiProvenanceWorkflowContractTests(unittest.TestCase):
    def test_every_required_job_definition_invokes_provenance_checker(self):
        workflow = TEST_WORKFLOW.read_text(encoding="utf-8")
        jobs = _job_blocks(workflow)
        self.assertEqual(set(jobs), set(REQUIRED_JOBS))
        for name in REQUIRED_JOBS:
            with self.subTest(job=name):
                self.assertEqual(len(RUN_PATTERN.findall(jobs[name])), 1)

        total = sum(len(RUN_PATTERN.findall(text)) for text in _workflow_texts())
        self.assertEqual(total, len(REQUIRED_JOBS))

    def test_job_block_parser_keeps_steps_in_their_own_jobs(self):
        workflow = """jobs:
  alpha:
    steps:
      - run: python scripts/check_ci_provenance.py
  beta:
    steps:
      - run: echo ok
"""
        jobs = _job_blocks(workflow)
        self.assertEqual(set(jobs), {"alpha", "beta"})
        self.assertEqual(len(RUN_PATTERN.findall(jobs["alpha"])), 1)
        self.assertEqual(len(RUN_PATTERN.findall(jobs["beta"])), 0)


class CommitObjectParserTests(unittest.TestCase):
    def test_reads_ordered_parents_from_raw_merge_commit(self):
        raw = (
            f"tree {TREE}\n"
            f"parent {BASE}\n"
            f"parent {HEAD}\n"
            "author Example <example@example.com> 0 +0000\n"
            "committer Example <example@example.com> 0 +0000\n"
            "\nMerge\n"
        )
        self.assertEqual(parse_commit_parents(raw), (BASE, HEAD))

    def test_reads_parent_even_when_parent_object_need_not_be_available(self):
        raw = f"tree {TREE}\nparent {BASE}\n\nmessage\n"
        self.assertEqual(parse_commit_parents(raw), (BASE,))

    def test_rejects_missing_tree_header(self):
        with self.assertRaisesRegex(ValueError, "missing tree"):
            parse_commit_parents(f"parent {BASE}\n\nmessage\n")

    def test_rejects_malformed_parent_header(self):
        with self.assertRaisesRegex(ValueError, "commit parent"):
            parse_commit_parents(f"tree {TREE}\nparent not-a-sha\n\nmessage\n")


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
