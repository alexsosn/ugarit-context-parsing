from __future__ import annotations

import json
import unittest
from dataclasses import replace
from types import MappingProxyType

from ugarit_context_parsing.alignment import (
    align_burns_source,
    alignment_report_json,
    build_alignment_report,
)
from ugarit_context_parsing.annotations import normalize_workbook_records
from ugarit_context_parsing.cuc_index import CucCompatibility, ReviewedCucIndex
from ugarit_context_parsing.source import WorkbookRecord


def record(
    *,
    source_row: int,
    source_page: int,
    headword: str,
    references: str,
    comments: str = "",
) -> WorkbookRecord:
    return WorkbookRecord(
        source_file="01 Synthetic/Worksheet 1.csv",
        source_row=source_row,
        source_page=source_page,
        section="Section α",
        root="",
        headword=headword,
        ktu="1.14",
        references=references,
        locus="GP",
        room=str(source_row),
        point="",
        depth="",
        disputed="",
        comments=comments,
    )


def index() -> ReviewedCucIndex:
    compatibility = CucCompatibility(
        repository="DT-UCPH/cuc",
        commit="ad69400f5446e1c8217af01659c7c10ab00c015b",
        version="0.2.8",
        manifest_sha256="717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba",
        files=(),
    )
    return ReviewedCucIndex(
        compatibility=compatibility,
        tablet_nodes=MappingProxyType({"KTU 1.14": 100}),
        column_nodes=MappingProxyType({("KTU 1.14", "I"): 110}),
        line_nodes=MappingProxyType(
            {
                ("KTU 1.14", "I", 2): 202,
                ("KTU 1.14", "I", 3): 203,
            }
        ),
        bare_line_candidates=MappingProxyType(
            {
                ("KTU 1.14", 2): (202,),
                ("KTU 1.14", 3): (203,),
            }
        ),
        line_words=MappingProxyType(
            {
                202: (310, 311, 312),
                203: (320, 321, 322),
            }
        ),
        word_g_cons=MappingProxyType(
            {
                310: "w",
                311: "bʿl",
                312: "x",
                320: "bʿl",
                321: "mlk",
                322: "x",
            }
        ),
    )


def normalized_source():
    return normalize_workbook_records(
        (
            record(source_row=1, source_page=7, headword="bʿl", references="I.2"),
            record(
                source_row=2,
                source_page=8,
                headword="bʿl mlk",
                references="I.3",
                comments="synthetic punctuation; newline\nkept locally",
            ),
        )
    )


class AlignmentReportTests(unittest.TestCase):
    def setUp(self):
        self.source = normalized_source()
        self.index = index()
        self.alignments = align_burns_source(self.source, self.index)

    def test_report_accounts_for_each_semantic_annotation_exactly_once(self):
        report = build_alignment_report(self.source, self.alignments, self.index)
        self.assertEqual(report["schema"], "burns-cuc-alignment-report-v1")
        self.assertEqual(report["counts"]["records"], 2)
        self.assertEqual(report["counts"]["annotations"], 2)
        self.assertEqual(report["counts"]["dispositions"], {"aligned": 2})

        entries = report["annotations"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            {entry["annotation_id"] for entry in entries},
            {item.annotation_id for item in self.source.annotations},
        )
        self.assertEqual(len({entry["annotation_id"] for entry in entries}), 2)

    def test_report_top_level_units_are_annotations_with_ordered_record_provenance(self):
        report = build_alignment_report(self.source, self.alignments, self.index)
        entries = report["annotations"]
        by_id = {entry["annotation_id"]: entry for entry in entries}

        for annotation in self.source.annotations:
            entry = by_id[annotation.annotation_id]
            self.assertEqual(entry["record_ids"], list(annotation.record_ids))
            self.assertEqual(
                [item["record_id"] for item in entry["source_records"]],
                list(annotation.record_ids),
            )

        first = by_id[self.source.annotations[0].annotation_id]
        self.assertEqual(
            first["source_records"],
            [
                {
                    "record_id": self.source.records[0].record_id,
                    "source_file": "01 Synthetic/Worksheet 1.csv",
                    "source_row": 1,
                    "source_page": 7,
                }
            ],
        )

    def test_multiword_span_is_one_occurrence_with_complete_ordered_nodes(self):
        report = build_alignment_report(self.source, self.alignments, self.index)
        second_id = self.source.annotations[1].annotation_id
        entry = next(item for item in report["annotations"] if item["annotation_id"] == second_id)
        self.assertEqual(len(entry["occurrences"]), 1)
        occurrence = entry["occurrences"][0]
        self.assertEqual(occurrence["anchor_kind"], "word_span")
        self.assertEqual(occurrence["anchor_nodes"], [320, 321])

    def test_compatibility_identity_is_embedded_without_cuc_payload(self):
        report = build_alignment_report(self.source, self.alignments, self.index)
        self.assertEqual(
            report["cuc_compatibility"],
            {
                "repository": "DT-UCPH/cuc",
                "commit": "ad69400f5446e1c8217af01659c7c10ab00c015b",
                "version": "0.2.8",
                "manifest_sha256": "717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba",
            },
        )

    def test_report_json_is_byte_deterministic_and_compact(self):
        a = alignment_report_json(self.source, self.alignments, self.index)
        b = alignment_report_json(self.source, tuple(reversed(self.alignments)), self.index)
        self.assertEqual(a, b)
        self.assertNotIn(": ", a)
        self.assertEqual(json.loads(a), build_alignment_report(self.source, self.alignments, self.index))

    def test_report_never_serializes_source_root_or_absolute_paths(self):
        payload = alignment_report_json(self.source, self.alignments, self.index)
        self.assertNotIn("source_root", payload)
        self.assertNotIn("/tmp/", payload)
        self.assertNotIn("\\\\", payload)

    def test_duplicate_alignment_id_fails_closed(self):
        duplicated = (self.alignments[0], self.alignments[0], self.alignments[1])
        with self.assertRaises(ValueError):
            build_alignment_report(self.source, duplicated, self.index)

    def test_missing_or_extra_alignment_id_fails_closed(self):
        with self.assertRaises(ValueError):
            build_alignment_report(self.source, self.alignments[:1], self.index)

        extra = replace(
            self.alignments[0],
            annotation_id="burns-annotation-sha256:extra",
        )
        with self.assertRaises(ValueError):
            build_alignment_report(self.source, (*self.alignments, extra), self.index)

    def test_changed_alignment_record_provenance_fails_closed(self):
        changed = replace(
            self.alignments[0],
            record_ids=("burns-record-sha256:not-the-source",),
        )
        with self.assertRaises(ValueError):
            build_alignment_report(self.source, (changed, self.alignments[1]), self.index)

    def test_missing_source_record_referenced_by_annotation_fails_closed(self):
        broken_source = replace(self.source, records=self.source.records[1:])
        with self.assertRaises(ValueError):
            build_alignment_report(broken_source, self.alignments, self.index)

    def test_unreferenced_source_record_fails_closed(self):
        extra_record = replace(
            self.source.records[0],
            record_id="burns-record-sha256:unreferenced",
            source_row=99,
        )
        broken_source = replace(self.source, records=(*self.source.records, extra_record))
        with self.assertRaises(ValueError):
            build_alignment_report(broken_source, self.alignments, self.index)

    def test_one_source_record_cannot_be_claimed_by_two_annotations(self):
        shared_record_id = self.source.records[0].record_id
        changed_annotation = replace(
            self.source.annotations[1],
            record_ids=(shared_record_id,),
        )
        broken_source = replace(
            self.source,
            annotations=(self.source.annotations[0], changed_annotation),
        )
        changed_alignment = replace(
            self.alignments[1],
            record_ids=(shared_record_id,),
        )
        with self.assertRaises(ValueError):
            build_alignment_report(
                broken_source,
                (self.alignments[0], changed_alignment),
                self.index,
            )

    def test_modified_selected_anchor_cannot_be_serialized_as_authoritative(self):
        changed_occurrence = replace(
            self.alignments[0].occurrences[0],
            anchor_nodes=(999999,),
        )
        changed_alignment = replace(
            self.alignments[0],
            occurrences=(changed_occurrence,),
        )
        with self.assertRaises(ValueError):
            build_alignment_report(
                self.source,
                (changed_alignment, self.alignments[1]),
                self.index,
            )

    def test_alignment_entries_sort_by_source_semantics_not_input_alignment_order(self):
        report = build_alignment_report(self.source, tuple(reversed(self.alignments)), self.index)
        self.assertEqual(
            [entry["annotation_id"] for entry in report["annotations"]],
            [annotation.annotation_id for annotation in self.source.annotations],
        )


if __name__ == "__main__":
    unittest.main()
