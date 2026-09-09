from __future__ import annotations

import copy
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


def _fixture():
    source = normalize_workbook_records(
        (
            WorkbookRecord(
                source_file="01 Synthetic/Worksheet 1.csv",
                source_row=1,
                source_page=7,
                section="Section α",
                root="rα",
                headword="w bʿl",
                ktu="1.14",
                references="I.2",
                locus="Lα",
                room="R1",
                point="p:1",
                depth="synthetic",
                disputed="?",
                comments="original synthetic report row",
            ),
        )
    )
    index = _index()
    alignments = align_burns_source(source, index)
    module = build_burns_module(source, alignments, index)
    report = build_burns_module_report(source, alignments, index, module)
    return source, module, report


def _mutable_module(module: BurnsModuleData) -> tuple[dict[str, dict[int, str]], dict[str, dict[str, str]]]:
    return (
        {feature: dict(values) for feature, values in module.node_features.items()},
        {feature: dict(values) for feature, values in module.metadata.items()},
    )


class BurnsTfModuleReportConsistencyAdversarialTests(unittest.TestCase):
    def test_writer_rejects_forged_annotation_count_before_fabric(self):
        _, module, report = _fixture()
        forged_report = copy.deepcopy(report)
        forged_report["counts"]["annotations"] = 999

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "annotation"):
                write_burns_module(
                    module,
                    forged_report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_alignment_anchor_disagreeing_with_module(self):
        _, module, report = _fixture()
        forged_report = copy.deepcopy(report)
        occurrence = forged_report["alignment"]["annotations"][0]["occurrences"][0]
        occurrence["anchor_nodes"] = [999]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "anchor|occurrence|alignment"):
                write_burns_module(
                    module,
                    forged_report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_node_source_row_disagreeing_with_report_inventory(self):
        _, module, report = _fixture()
        node_features, metadata = _mutable_module(module)
        for node in (310, 311):
            payloads = json.loads(node_features["burns_annotations"][node])
            self.assertEqual(len(payloads), 1)
            payloads[0]["source_records"][0]["comments"] = "forged but copy-consistent"
            node_features["burns_annotations"][node] = _canonical(payloads)
        forged_module = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "source record|provenance|record"):
                write_burns_module(
                    forged_module,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
