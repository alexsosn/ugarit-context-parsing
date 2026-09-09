from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "test.yml"
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
ACTION_REF_PATTERN = re.compile(
    r"actions/(?:checkout|setup-python)@[A-Za-z0-9._/-]+"
)


def _action_refs(workflow: str) -> list[str]:
    refs: list[str] = []
    for line in workflow.splitlines():
        code = line.split("#", 1)[0]
        refs.extend(ACTION_REF_PATTERN.findall(code))
    return refs


class CiActionPinTests(unittest.TestCase):
    def test_extractor_handles_quoted_refs_and_ignores_comments(self):
        workflow = """
          - uses: actions/checkout@v4
          - uses: 'actions/setup-python@v5'
          - uses: "actions/checkout@deadbeef"
          # - uses: actions/setup-python@ignored
        """
        self.assertEqual(
            _action_refs(workflow),
            [
                "actions/checkout@v4",
                "actions/setup-python@v5",
                "actions/checkout@deadbeef",
            ],
        )

    def test_checkout_and_setup_python_use_reviewed_immutable_releases(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        actual = Counter(_action_refs(workflow))
        expected = Counter({CHECKOUT: 5, SETUP_PYTHON: 3})
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
