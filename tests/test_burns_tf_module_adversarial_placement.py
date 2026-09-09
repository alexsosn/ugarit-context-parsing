from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from ugarit_context_parsing.alignment import align_burns_source
from ugarit_context_parsing.annotations import normalize_workbook_records
from ugarit_context_parsing.cuc_index import CucCompatibility, ReviewedCucIndex
from ugarit_context_parsing.module import (
    BurnsModuleData,
    build_burns_module,
    build_burns_module_report,
    write_burns_module,
)
from ugarit_context_parsing.source import WorkbookRecord


class _FabricMustNotBeConstructed:
    def __init__(self, **kwargs):
        raise AssertionError("writer validation ran after Fabric construction")


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _index() -> ReviewedCucIndex:
    return ReviewedCucIndex(
        compatibility=CucCompatibility(
            repository="DT-UCPH/cuc",
            commit="ad69400f5446e1c8217af01659c7c10ab00c015b",
            version="0.2.8",
            manifest_sha256="717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba",
            files=(),
        ),
        tablet_nodes=MappingProxyType({"KTU 1.14": 100}),
        column_nodes=MappingProxyType({("KTU 1.14", "I"): 110}),
        line_nodes=MappingProxyType({("KTU 1.14", "I", 2): 202}),
        bare_line_candidates=MappingProxyType({("KTU 1.14", 2): (202,)}),
        line_words=MappingProxyType({202: (310, 311)}),
        word_g_cons=MappingProxyType({310: "w", 311: "bʿl"}),
    )


def _record(*, headword: str, references: str, comments: str = "synthetic") -> WorkbookRecord:
    return WorkbookRecord(
        source_file="01 Synthetic/Worksheet 1.csv",
        source_row=1,
        source_page=7,
        section="Section α",
        root="rα",
        headword=headword,
        ktu="1.14",
        references=references,
        locus="Lα",
        room="R1",
        point="p:1",
        depth="deep\n2",
        disputed="?",
        comments=comments,
    )


def _span_fixture():
    source = normalize_workbook_records((_record(headword="w bʿl", references="I.2"),))
    index = _index()
    alignments = align_burns_source(source, index)
    module = build_burns_module(source, alignments, index)
    report = build_burns_module_report(source, alignments, index, module)
    return source, index, alignments, module, report


def _mutable_module(module: BurnsModuleData) -> tuple[dict[str, dict[int, str]], dict[str, dict[str, str]]]:
    return (
        {feature: dict(values) for feature, values in module.node_features.items()},
        {feature: dict(values) for feature, values in module.metadata.items()},
    )


class BurnsTfModulePlacementAdversarialTests(unittest.TestCase):
    def test_writer_rejects_payload_moved_to_node_outside_its_anchor_tuple(self):
        _, _, _, module, report = _span_fixture()
        node_features, metadata = _mutable_module(module)
        for values in node_features.values():
            values[999] = values.pop(310)
        forged = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "placement|anchor"):
                write_burns_module(
                    forged,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_missing_participating_copy_of_multiword_span(self):
        _, _, _, module, report = _span_fixture()
        node_features, metadata = _mutable_module(module)
        for values in node_features.values():
            values.pop(311)
        forged = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "complete|anchor|placement"):
                write_burns_module(
                    forged,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_divergent_copies_with_same_occurrence_identity(self):
        _, _, _, module, report = _span_fixture()
        node_features, metadata = _mutable_module(module)
        payloads = json.loads(node_features["burns_annotations"][311])
        payloads[0]["source_records"][0]["comments"] = "forged divergent copy"
        node_features["burns_annotations"][311] = _canonical(payloads)
        forged = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "copies|identity|payload"):
                write_burns_module(
                    forged,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_unresolved_record_remains_fully_available_in_module_report(self):
        source = normalize_workbook_records(
            (
                _record(
                    headword="unresolved α",
                    references="I.99",
                    comments='unresolved "quoted"\ncomment',
                ),
            )
        )
        index = _index()
        alignments = align_burns_source(source, index)
        self.assertEqual(alignments[0].disposition.value, "unresolved_reference")
        module = build_burns_module(source, alignments, index)
        self.assertEqual(dict(module.node_features["burns_annotations"]), {})
        report = build_burns_module_report(source, alignments, index, module)

        self.assertEqual(len(report["source_records"]), 1)
        row = report["source_records"][0]
        record = source.records[0]
        self.assertEqual(
            row,
            {
                "record_id": record.record_id,
                "source_file": "01 Synthetic/Worksheet 1.csv",
                "source_row": 1,
                "source_page": 7,
                "section": "Section α",
                "root": "rα",
                "headword": "unresolved α",
                "ktu": "1.14",
                "references": "I.99",
                "locus": "Lα",
                "room": "R1",
                "point": "p:1",
                "depth": "deep\n2",
                "disputed": "?",
                "comments": 'unresolved "quoted"\ncomment',
                "worksheet_id": record.worksheet_id,
                "workbook_number": 1,
                "workbook_label": record.workbook_label,
                "worksheet_number": 1,
                "worksheet_role": record.worksheet_role.value,
                "textual_status": record.textual_status.value,
                "semantic_status": record.semantic_status.value,
                "interpretive_status": record.interpretive_status.value,
            },
        )
        self.assertEqual(report["alignment"]["annotations"][0]["record_ids"], [record.record_id])


if __name__ == "__main__":
    unittest.main()
