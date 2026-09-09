from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "test.yml"
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
USES_PATTERN = re.compile(
    r"^\s*(?:-\s*)?uses:\s*(actions/(?:checkout|setup-python)@[^\s#]+)",
    re.MULTILINE,
)


class CiActionPinTests(unittest.TestCase):
    def test_checkout_and_setup_python_use_reviewed_immutable_releases(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        actual = Counter(USES_PATTERN.findall(workflow))
        expected = Counter({CHECKOUT: 5, SETUP_PYTHON: 3})
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
