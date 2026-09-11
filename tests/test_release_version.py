from importlib import metadata
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "0.3.0"
EXPECTED_MATERIALIZERS = [
    "burns-workbooks-csv-text-fabric",
    "burns-workbooks-pdf-text-fabric",
]


class ReleaseVersionContractTests(unittest.TestCase):
    def test_installed_package_uses_release_version(self):
        self.assertEqual(metadata.version("ugarit-context-parsing"), TARGET_VERSION)

    def test_materializer_manifest_uses_same_release_version_and_identity(self):
        manifest = json.loads((ROOT / "agora.materializer.json").read_text(encoding="utf-8"))
        plugin = manifest["plugin"]
        self.assertEqual(plugin["version"], TARGET_VERSION)
        self.assertEqual(plugin["id"], "ugarit-context-parsing")
        self.assertEqual(plugin["repository"], "alexsosn/ugarit-context-parsing")
        self.assertEqual(
            [entry["id"] for entry in manifest["materializers"]],
            EXPECTED_MATERIALIZERS,
        )


if __name__ == "__main__":
    unittest.main()
