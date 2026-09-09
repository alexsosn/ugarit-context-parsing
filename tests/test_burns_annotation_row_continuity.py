from __future__ import annotations

import unittest

from ugarit_context_parsing.annotations import BurnsNormalizationError, normalize_workbook_records
from ugarit_context_parsing.source import WorkbookRecord


WORKBOOK_I = "01 Workbook I - Divine Names (DNs)"


def _record(*, source_row: int, source_file: str | None = None) -> WorkbookRecord:
    return WorkbookRecord(
        source_file=source_file or f"{WORKBOOK_I}/Worksheet 1.csv",
        source_row=source_row,
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
        comments="synthetic continuity gate",
    )


class BurnsAnnotationRowContinuityTests(unittest.TestCase):
    def test_missing_source_row_breaks_otherwise_identical_annotation_group(self):
        result = normalize_workbook_records((_record(source_row=1), _record(source_row=3)))

        self.assertEqual(len(result.annotations), 2)
        self.assertEqual(result.annotations[0].first_source_row, 1)
        self.assertEqual(result.annotations[1].first_source_row, 3)
        self.assertNotEqual(
            result.annotations[0].annotation_id,
            result.annotations[1].annotation_id,
        )

    def test_consecutive_rows_with_same_textual_key_still_group(self):
        result = normalize_workbook_records((_record(source_row=1), _record(source_row=2)))

        self.assertEqual(len(result.annotations), 1)
        self.assertEqual(len(result.annotations[0].record_ids), 2)

    def test_backwards_rows_in_one_worksheet_fail_closed_instead_of_sorting(self):
        with self.assertRaisesRegex(BurnsNormalizationError, r"(?i)(order|row|monotonic)"):
            normalize_workbook_records((_record(source_row=2), _record(source_row=1)))

    def test_new_worksheet_may_restart_row_numbering_and_starts_new_group(self):
        result = normalize_workbook_records(
            (
                _record(source_row=2, source_file=f"{WORKBOOK_I}/Worksheet 1.csv"),
                _record(source_row=1, source_file=f"{WORKBOOK_I}/Worksheet 2.csv"),
            )
        )

        self.assertEqual(len(result.annotations), 2)
        self.assertNotEqual(
            result.annotations[0].worksheet_id,
            result.annotations[1].worksheet_id,
        )


if __name__ == "__main__":
    unittest.main()
