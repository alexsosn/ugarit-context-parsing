from __future__ import annotations

import unittest

from ugarit_context_parsing.annotations import BurnsNormalizationError, normalize_workbook_records
from ugarit_context_parsing.source import WorkbookRecord


WORKBOOK = "01 Workbook I - Divine Names (DNs)"


def _record(source_file: str) -> WorkbookRecord:
    return WorkbookRecord(
        source_file=source_file,
        source_row=1,
        source_page=1,
        section="Section α",
        root="",
        headword="bʿl",
        ktu="1.14",
        references="I 1",
        locus="GP",
        room="1",
        point="",
        depth="",
        disputed="n",
        comments="synthetic prefixed-filename regression",
    )


class PrefixedWorksheetFilenameTests(unittest.TestCase):
    def test_real_shaped_pdf_and_csv_names_are_adapter_neutral(self):
        pdf = normalize_workbook_records((_record(f"{WORKBOOK}/DNs Worksheet 1.pdf"),))
        csv = normalize_workbook_records((_record(f"{WORKBOOK}/DNs Worksheet 1.csv"),))

        expected = f"{WORKBOOK}/DNs Worksheet 1"
        self.assertEqual(pdf.records[0].worksheet_id, expected)
        self.assertEqual(csv.records[0].worksheet_id, expected)
        self.assertEqual(pdf.records[0].record_id, csv.records[0].record_id)
        self.assertEqual(pdf.annotations[0].annotation_id, csv.annotations[0].annotation_id)
        self.assertEqual(pdf.records[0].worksheet_number, 1)

    def test_terminal_worksheet_token_is_required(self):
        invalid = (
            f"{WORKBOOK}/DNs Worksheet 1 copy.pdf",
            f"{WORKBOOK}/DNs Worksheet.pdf",
            f"{WORKBOOK}/DNs Worksheet 6.pdf",
        )
        for source_file in invalid:
            with self.subTest(source_file=source_file):
                with self.assertRaises(BurnsNormalizationError):
                    normalize_workbook_records((_record(source_file),))


if __name__ == "__main__":
    unittest.main()
