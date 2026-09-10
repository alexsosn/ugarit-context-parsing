from __future__ import annotations

import json
import unittest
from importlib.metadata import version as installed_version
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_FEATURES = [
    "burns_annotations.tf",
    "burns_annotation_ids.tf",
    "burns_semantic_statuses.tf",
    "burns_worksheet_roles.tf",
    "burns_sections.tf",
    "burns_headwords.tf",
    "burns-module-report.json",
]
LEGACY_OUTPUTS = ["otype.tf", "oslots.tf", "otext.tf", "conversion-report.json"]


class BurnsAgoraProductManifestRedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "agora.materializer.json").read_text(encoding="utf-8"))
        cls.items = {item["id"]: item for item in cls.manifest["materializers"]}

    def test_product_exposes_new_module_ids_before_legacy_compatibility_ids(self):
        self.assertEqual(
            [item["id"] for item in self.manifest["materializers"]],
            [
                "burns-workbooks-csv-cuc-module",
                "burns-workbooks-pdf-cuc-module",
                "burns-workbooks-csv-text-fabric",
                "burns-workbooks-pdf-text-fabric",
            ],
        )

    def test_new_module_entries_use_existing_module_cli_and_exact_parent_contract(self):
        for source_format, glob in (("csv", "*/*.csv"), ("pdf", "*/*.pdf")):
            materializer_id = f"burns-workbooks-{source_format}-cuc-module"
            with self.subTest(materializer=materializer_id):
                item = self.items[materializer_id]
                self.assertEqual(item["input"]["required_globs"], [glob])
                self.assertFalse(item["input"]["allow_symlinks"])
                self.assertEqual(item["acquisition"][0]["type"], "user-local")
                self.assertEqual(
                    item["execution"],
                    {
                        "type": "python-module",
                        "module": "ugarit_context_parsing.cli",
                        "args": [
                            "module",
                            "{source}",
                            "--input-format",
                            source_format,
                            "--cuc",
                            "{parent}",
                            "--output",
                            "{output}",
                        ],
                        "network": "deny",
                    },
                )
                self.assertEqual(
                    item["output"],
                    {
                        "format": "text-fabric",
                        "required_paths": MODULE_FEATURES,
                        "composition": {
                            "kind": "feature-module",
                            "parent": "cuc",
                            "compatibility": {"parent_versions": ["0.2.8"]},
                        },
                    },
                )
                for forbidden in ("otype.tf", "oslots.tf", "otext.tf"):
                    self.assertNotIn(forbidden, item["output"]["required_paths"])

    def test_legacy_ids_remain_behaviorally_compatible_and_explicitly_deprecated(self):
        for source_format, glob in (("csv", "*/*.csv"), ("pdf", "*/*.pdf")):
            materializer_id = f"burns-workbooks-{source_format}-text-fabric"
            with self.subTest(materializer=materializer_id):
                item = self.items[materializer_id]
                self.assertIn("deprecat", item["description"].casefold())
                self.assertEqual(item["input"]["required_globs"], [glob])
                self.assertFalse(item["input"]["allow_symlinks"])
                self.assertEqual(item["execution"]["module"], "ugarit_context_parsing.cli")
                self.assertEqual(
                    item["execution"]["args"],
                    [
                        "convert",
                        "{source}",
                        "--input-format",
                        source_format,
                        "--output",
                        "{output}",
                    ],
                )
                self.assertEqual(item["execution"]["network"], "deny")
                self.assertEqual(item["output"]["required_paths"], LEGACY_OUTPUTS)
                self.assertNotIn("composition", item["output"])

    def test_ticket_does_not_smuggle_a_release_or_version_change(self):
        self.assertEqual(installed_version("ugarit-context-parsing"), "0.2.0")
        self.assertEqual(self.manifest["plugin"]["version"], "0.2.0")


if __name__ == "__main__":
    unittest.main()
