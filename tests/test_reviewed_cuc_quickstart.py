from __future__ import annotations

import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CUC_COMMIT = "ad69400f5446e1c8217af01659c7c10ab00c015b"
CUC_REMOTE = "https://github.com/DT-UCPH/cuc.git"


def _materialization_section() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    marker = "## Materializing a CUC-aligned Burns feature module\n"
    if marker not in readme:
        raise AssertionError("README has no CUC module materialization section")
    return readme.split(marker, 1)[1].split("\n## ", 1)[0]


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class ReviewedCucQuickstartDocumentationTests(unittest.TestCase):
    def test_quickstart_pins_exact_reviewed_cuc_without_following_main(self):
        section = _materialization_section()
        normalized = _normalized(section)

        self.assertIn("python -m pip install .", normalized)
        self.assertIn(CUC_REMOTE, section)
        self.assertIn(CUC_COMMIT, section)
        self.assertIn(
            f"git clone --filter=blob:none --no-checkout {CUC_REMOTE} cuc",
            normalized,
        )
        self.assertIn(
            f"git -C cuc checkout --detach {CUC_COMMIT}",
            normalized,
        )

    def test_quickstart_does_not_depend_on_raw_sha_fetch_policy(self):
        section = _materialization_section()
        normalized = _normalized(section)

        self.assertNotIn(f"fetch --depth 1 origin {CUC_COMMIT}", normalized)
        self.assertNotIn("checkout --detach FETCH_HEAD", normalized)

    def test_first_runnable_module_path_uses_checked_out_reviewed_cuc(self):
        section = _materialization_section()
        normalized = _normalized(section)

        self.assertIn("ugarit-context-parsing module output", normalized)
        self.assertIn("--input-format csv", normalized)
        self.assertIn("--cuc cuc/tf/0.2.8", normalized)
        self.assertIn("--output tf/burns-module", normalized)

    def test_network_and_agora_boundaries_remain_explicit(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section = _materialization_section().casefold()
        agora = readme.split("### Agora status\n", 1)[1].split("\n### ", 1)[0].casefold()

        self.assertIn("does not download cuc", section)
        self.assertTrue("user" in section and "acqui" in section)
        self.assertTrue("deferred" in agora or "not planned" in agora)
        self.assertNotIn("parent-aware module is registered", agora)


if __name__ == "__main__":
    unittest.main()
