from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.pdf_source import load_pdf_directory, parse_workbook_pdf
from ugarit_context_parsing.source import WorkbookRecord, WorkbookSource


class PdfSourceTests(unittest.TestCase):
    @staticmethod
    def _row(headword: str, ktu: str, page: int = 1) -> dict[str, object]:
        return {
            "source_page": page,
            "section": "Section α",
            "root": "",
            "headword": headword,
            "ktu": ktu,
            "references": "synthetic",
            "locus": "GP",
            "room": "",
            "point": "",
            "depth": "",
            "disputed": "n",
            "comments": "synthetic",
        }

    def test_pdf_loader_discovers_stably_and_feeds_existing_parser_results(self):
        calls: list[str] = []

        def fake_parser(path: Path):
            calls.append(path.name)
            return [self._row(path.stem, "1.14" if path.stem == "A" else "1.15")]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("Z/B.pdf", "A/A.pdf"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic pdf bytes")

            source = load_pdf_directory(root, parser=fake_parser)

        self.assertEqual(calls, ["A.pdf", "B.pdf"])
        self.assertEqual(source.files, ("A/A.pdf", "Z/B.pdf"))
        self.assertEqual([record.source_file for record in source.records], ["A/A.pdf", "Z/B.pdf"])
        self.assertEqual([record.source_row for record in source.records], [1, 1])
        self.assertEqual([record.headword for record in source.records], ["A", "B"])
        self.assertRegex(source.tree_sha256, r"^[0-9a-f]{64}$")

    def test_public_pdf_parser_adapter_points_at_the_existing_workbook_parser(self):
        self.assertTrue(callable(parse_workbook_pdf))
        self.assertEqual(parse_workbook_pdf.__name__, "parse_workbook_pdf")

    @mock.patch("ugarit_context_parsing.cli.write_artifact")
    @mock.patch("ugarit_context_parsing.cli.load_pdf_directory")
    def test_pdf_cli_uses_same_graph_report_and_writer_path(self, load_pdf_mock, write_mock):
        write_mock.return_value = True
        records = (
            WorkbookRecord(
                source_file="Workbook/A.pdf",
                source_row=1,
                source_page=1,
                section="Section α",
                root="",
                headword="bʿl",
                ktu="1.14",
                references="synthetic",
                locus="GP",
                room="",
                point="",
                depth="",
                disputed="n",
                comments="synthetic",
            ),
        )
        load_pdf_mock.return_value = WorkbookSource(
            root=Path("/not/serialized"),
            records=records,
            files=("Workbook/A.pdf",),
            tree_sha256="a" * 64,
        )

        result = main([
            "convert",
            "/chosen/source",
            "--input-format",
            "pdf",
            "--output",
            "/chosen/output",
        ])

        self.assertEqual(result, 0)
        load_pdf_mock.assert_called_once_with(Path("/chosen/source"))
        self.assertEqual(write_mock.call_count, 1)
        data, report, output = write_mock.call_args.args[:3]
        self.assertEqual(data.max_slot, 1)
        self.assertEqual(report["source"]["format"], "pdf")
        self.assertEqual(output, Path("/chosen/output"))


if __name__ == "__main__":
    unittest.main()
