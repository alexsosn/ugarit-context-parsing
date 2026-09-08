from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from ugarit_context_parsing.pdf_source import load_pdf_directory
from ugarit_context_parsing.source import (
    WORKBOOK_FIELDS,
    SourceValidationError,
    load_csv_directory,
)


def _workbook_row() -> dict[str, object]:
    return {
        "source_page": 1,
        "section": "Section synthetic",
        "root": "",
        "headword": "synthetic",
        "ktu": "1.14",
        "references": "I 1",
        "locus": "GP",
        "room": "1",
        "point": "",
        "depth": "",
        "disputed": "n",
        "comments": "synthetic test row",
    }


def _write_csv_source(root: Path) -> None:
    csv_path = root / "Workbook" / "Worksheet.csv"
    csv_path.parent.mkdir(parents=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORKBOOK_FIELDS)
        writer.writeheader()
        writer.writerow(_workbook_row())


def _make_directory_symlink(link: Path, target: Path, testcase: unittest.TestCase) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        testcase.skipTest(f"symlinks unavailable: {exc}")


class SourceRootSymlinkTests(unittest.TestCase):
    def test_csv_loader_rejects_symlink_supplied_as_source_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_root = base / "real-csv"
            _write_csv_source(real_root)

            link_root = base / "linked-csv"
            _make_directory_symlink(link_root, real_root, self)

            with self.assertRaisesRegex(SourceValidationError, "symlink"):
                load_csv_directory(link_root)

    def test_pdf_loader_rejects_symlink_supplied_as_source_root(self):
        def fake_parser(path: Path) -> list[dict[str, object]]:
            return [_workbook_row()]

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_root = base / "real-pdf"
            pdf_path = real_root / "Workbook" / "Worksheet.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_path.write_bytes(b"synthetic pdf bytes")

            link_root = base / "linked-pdf"
            _make_directory_symlink(link_root, real_root, self)

            with self.assertRaisesRegex(SourceValidationError, "symlink"):
                load_pdf_directory(link_root, parser=fake_parser)

    def test_dangling_symlink_source_root_reports_symlink_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            link_root = base / "dangling-source"
            _make_directory_symlink(link_root, base / "missing-target", self)
            self.assertTrue(link_root.is_symlink())

            with self.assertRaisesRegex(SourceValidationError, "symlink"):
                load_csv_directory(link_root)

    def test_real_leaf_below_symlinked_ancestor_remains_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_parent = base / "real-parent"
            real_root = real_parent / "source"
            _write_csv_source(real_root)

            linked_parent = base / "linked-parent"
            _make_directory_symlink(linked_parent, real_parent, self)
            supplied_root = linked_parent / "source"
            self.assertFalse(supplied_root.is_symlink())

            source = load_csv_directory(supplied_root)
            self.assertEqual(source.root, real_root.resolve())
            self.assertEqual(source.files, ("Workbook/Worksheet.csv",))

    def test_normal_missing_source_root_keeps_directory_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing-source"
            with self.assertRaisesRegex(SourceValidationError, "does not exist"):
                load_csv_directory(missing)


if __name__ == "__main__":
    unittest.main()
