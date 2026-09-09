from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from unittest import mock


parser = importlib.import_module("scripts.parse_workbooks_to_csv")


def cells(**values: str) -> dict[str, str]:
    row = {column: "" for column in parser.COLS}
    row.update(values)
    return row


class WorkbookParserStructureTests(unittest.TestCase):
    def parse_lines(
        self,
        lines: list[tuple[int, dict[str, str]]],
        *,
        parent: str,
    ) -> list[dict[str, str]]:
        fake_pdf = mock.MagicMock()
        fake_pdf.__enter__.return_value = object()
        fake_pdf.__exit__.return_value = False
        with (
            mock.patch.object(parser.pdfplumber, "open", return_value=fake_pdf),
            mock.patch.object(parser, "file_bounds", return_value=parser.CANONICAL_BOUNDS),
            mock.patch.object(parser, "_content_lines", return_value=lines),
        ):
            return parser.parse_pdf(Path(parent) / "Synthetic.pdf")

    def test_non_actions_a_only_line_continues_open_headword_before_new_anchor(self):
        rows = self.parse_lines(
            [
                (1, cells(A="alpha", B="1")),
                (1, cells(A="tail")),
                (1, cells(A="beta", B="2")),
            ],
            parent="VII Synthetic Workbook",
        )

        self.assertEqual(rows[0]["headword"], "alpha tail")
        self.assertEqual(rows[0]["root"], "")
        self.assertEqual(rows[1]["headword"], "beta")
        self.assertEqual(rows[1]["root"], "")

    def test_actions_same_local_shape_remains_root_grouping(self):
        rows = self.parse_lines(
            [
                (1, cells(A="form-one", B="1")),
                (1, cells(A="root-label")),
                (1, cells(A="form-two", B="2")),
            ],
            parent="IX Synthetic Workbook",
        )

        self.assertEqual(rows[0]["headword"], "form-one")
        self.assertEqual(rows[1]["headword"], "form-two")
        self.assertEqual(rows[1]["root"], "root-label")

    def test_blank_a_anchor_keeps_existing_definite_wrap_behavior(self):
        rows = self.parse_lines(
            [
                (1, cells(A="alpha", B="1")),
                (1, cells(A="tail")),
                (1, cells(D="GP")),
            ],
            parent="VII Synthetic Workbook",
        )

        self.assertEqual([row["headword"] for row in rows], ["alpha tail", "alpha tail"])
        self.assertEqual([row["root"] for row in rows], ["", ""])

    def test_bracket_balance_keeps_existing_definite_wrap_behavior(self):
        rows = self.parse_lines(
            [
                (1, cells(A="alpha (", B="1")),
                (1, cells(A="tail)")),
                (1, cells(A="beta", B="2")),
            ],
            parent="VII Synthetic Workbook",
        )

        self.assertEqual(rows[0]["headword"], "alpha ( tail)")
        self.assertEqual(rows[1]["root"], "")

    def test_page_boundary_does_not_break_non_actions_wrap(self):
        rows = self.parse_lines(
            [
                (1, cells(A="alpha", B="1")),
                (2, cells(A="tail")),
                (2, cells(A="beta", B="2")),
            ],
            parent="VII Synthetic Workbook",
        )
        self.assertEqual(rows[0]["headword"], "alpha tail")
        self.assertEqual(rows[1]["root"], "")

    def test_section_banner_clears_actions_root_group(self):
        rows = self.parse_lines(
            [
                (1, cells(A="root-label")),
                (1, cells(A="form-one", B="1")),
                (1, cells(A="Section beta")),
                (1, cells(A="form-two", B="2")),
            ],
            parent="IX Synthetic Workbook",
        )
        self.assertEqual(rows[0]["root"], "root-label")
        self.assertEqual(rows[1]["root"], "")

    def test_unknown_workbook_role_fails_closed_on_ambiguous_a_only_line(self):
        with self.assertRaises(parser.WorkbookStructureError):
            self.parse_lines(
                [
                    (1, cells(A="alpha", B="1")),
                    (1, cells(A="tail")),
                    (1, cells(A="beta", B="2")),
                ],
                parent="Synthetic Workbook",
            )

    def test_unknown_workbook_role_accepts_unambiguous_anchor_only_input(self):
        rows = self.parse_lines(
            [(1, cells(A="alpha", B="1"))],
            parent="Synthetic Workbook",
        )
        self.assertEqual(rows[0]["headword"], "alpha")
        self.assertEqual(rows[0]["root"], "")

    def test_workbook_ordinal_accepts_canonical_arabic_and_roman_prefixes(self):
        self.assertEqual(parser._workbook_ordinal(Path("7 Synthetic/Synthetic.pdf")), 7)
        self.assertEqual(parser._workbook_ordinal(Path("VII Synthetic/Synthetic.pdf")), 7)
        self.assertEqual(parser._workbook_ordinal(Path("IX Synthetic/Synthetic.pdf")), 9)

    def test_workbook_ordinal_rejects_unrelated_or_out_of_range_prefixes(self):
        self.assertIsNone(parser._workbook_ordinal(Path("Synthetic/Synthetic.pdf")))
        self.assertIsNone(parser._workbook_ordinal(Path("10 Synthetic/Synthetic.pdf")))
        self.assertIsNone(parser._workbook_ordinal(Path("X Synthetic/Synthetic.pdf")))


if __name__ == "__main__":
    unittest.main()
