from importlib import metadata
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SoftwareLicenseContractTests(unittest.TestCase):
    def test_repository_contains_standard_mit_license(self):
        license_path = ROOT / "LICENSE"
        self.assertTrue(license_path.is_file(), "repository must contain LICENSE")
        text = license_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License\n"))
        self.assertIn(
            "Copyright (c) 2026 Oleksandr (Alex) Sosnovshchenko",
            text,
        )
        self.assertIn(
            "Permission is hereby granted, free of charge, to any person obtaining a copy",
            text,
        )
        self.assertIn(
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND',
            text,
        )

    def test_installed_package_declares_mit_and_includes_license_file(self):
        package_metadata = metadata.metadata("ugarit-context-parsing")
        self.assertEqual(package_metadata.get("License-Expression"), "MIT")
        license_files = package_metadata.get_all("License-File") or []
        self.assertIn("LICENSE", license_files)

    def test_readme_separates_software_and_burns_data_terms(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.casefold().split())
        self.assertIn("software license", normalized)
        self.assertIn("mit", normalized)
        self.assertIn("cc by-nc-nd 2.5", normalized)
        self.assertIn("generated", normalized)
        self.assertIn("do not redistribute", normalized)
        self.assertIn("burns", normalized)


if __name__ == "__main__":
    unittest.main()
