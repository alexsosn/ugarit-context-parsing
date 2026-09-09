from __future__ import annotations

import re
import unittest
from pathlib import Path


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
PROVENANCE_COMMAND = "python scripts/check_ci_provenance.py"
RUN_PATTERN = re.compile(
    r"^\s*run:\s*['\"]?python scripts/check_ci_provenance\.py['\"]?\s*(?:#.*)?$",
    re.MULTILINE,
)


def _workflow_texts() -> list[str]:
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    return [path.read_text(encoding="utf-8") for path in paths]


class CiProvenanceWorkflowContractTests(unittest.TestCase):
    def test_every_required_job_definition_invokes_provenance_checker(self):
        count = sum(len(RUN_PATTERN.findall(text)) for text in _workflow_texts())
        self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
