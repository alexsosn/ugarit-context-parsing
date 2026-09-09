from __future__ import annotations

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
    burns_node_annotations,
    write_burns_module,
)
from ugarit_context_parsing.source import WorkbookRecord


class _FabricMustNotBeConstructed:
    def __init__(self, **kwargs):
        raise AssertionError("writer validation ran after Fabric construction")


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


def _source():
    return normalize_workbook_records(
        (
            WorkbookRecord(
                source_file="01 Synthetic/Worksheet 1.csv",
                source_row=1,
                source_page=1,
                section="Section α",
                root="",
                headword="bʿl",
                ktu="1.14",
                references="I.2,99",
                locus="SYN",
                room="1",
                point="p1",
                depth="synthetic",
                disputed="",
                comments="synthetic mixed-target adversarial fixture",
            ),
        )
    )


def _fixture():
    source = _source()
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


class BurnsTfModuleAdversarialTests(unittest.TestCase):
    def test_selected_payload_preserves_annotation_partiality_separately_from_occurrence_status(self):
        _, _, alignments, module, _ = _fixture()
        self.assertEqual(alignments[0].disposition.value, "partial")
        self.assertEqual(alignments[0].reason.value, "mixed_target_results")
        self.assertEqual(alignments[0].occurrences[0].disposition.value, "aligned")
        self.assertEqual(alignments[0].occurrences[1].anchor_nodes, ())

        payloads = burns_node_annotations(module.node_features["burns_annotations"][311])
        self.assertEqual(len(payloads), 1)
        payload = payloads[0]
        self.assertEqual(payload["disposition"], "aligned")
        self.assertEqual(payload["annotation_disposition"], "partial")
        self.assertEqual(payload["annotation_reason"], "mixed_target_results")

    def test_writer_rederives_projection_before_fabric_construction(self):
        _, _, _, module, report = _fixture()
        node_features, metadata = _mutable_module(module)
        node_features["burns_headwords"][311] = '["forged"]'
        forged = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "projection"):
                write_burns_module(
                    forged,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_forged_reviewed_cuc_feature_metadata_before_fabric(self):
        _, _, _, module, report = _fixture()
        node_features, metadata = _mutable_module(module)
        metadata["burns_annotations"]["cucCommit"] = "forged"
        forged = BurnsModuleData(node_features=node_features, metadata=metadata)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "metadata"):
                write_burns_module(
                    forged,
                    report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())

    def test_writer_rejects_forged_report_cuc_identity_before_fabric(self):
        _, _, _, module, report = _fixture()
        forged_report = dict(report)
        forged_compatibility = dict(report["cuc_compatibility"])
        forged_compatibility["commit"] = "forged"
        forged_report["cuc_compatibility"] = forged_compatibility

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            with self.assertRaisesRegex(ValueError, "compatibility"):
                write_burns_module(
                    module,
                    forged_report,
                    output,
                    fabric_factory=_FabricMustNotBeConstructed,
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
