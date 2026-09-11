from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import ugarit_context_parsing.cuc_index as cuc_index
from ugarit_context_parsing.alignment import align_burns_source
from ugarit_context_parsing.annotations import normalize_workbook_records
from ugarit_context_parsing.cuc_index import CucCompatibility, ReviewedCucIndex
from ugarit_context_parsing.module import build_burns_module, build_burns_module_report
from ugarit_context_parsing.source import WorkbookRecord


EXPECTED_SCHEMA = "burns-cuc-compatibility-v1"
EXPECTED_FEATURES = ["column", "g_cons", "line", "tablet"]
EXPECTED_COUNTS = {
    "column": 334,
    "line": 7616,
    "sign": 146017,
    "tablet": 279,
    "word": 27770,
}
EXPECTED_SECTION_TYPES = ["tablet", "column", "line"]
EXPECTED_SECTION_FEATURES = ["tablet", "column", "line"]


def _compatibility() -> CucCompatibility:
    return CucCompatibility(
        repository=cuc_index.REVIEWED_CUC_REPOSITORY,
        commit=cuc_index.REVIEWED_CUC_COMMIT,
        version=cuc_index.REVIEWED_CUC_VERSION,
        manifest_sha256=cuc_index.REVIEWED_CUC_MANIFEST_SHA256,
        files=(),
    )


def _index() -> ReviewedCucIndex:
    return ReviewedCucIndex(
        compatibility=_compatibility(),
        tablet_nodes=MappingProxyType({"KTU 1.14": 10}),
        column_nodes=MappingProxyType({("KTU 1.14", "I"): 9}),
        line_nodes=MappingProxyType({("KTU 1.14", "I", 2): 8}),
        bare_line_candidates=MappingProxyType({("KTU 1.14", 2): (8,)}),
        line_words=MappingProxyType({8: (7,)}),
        word_g_cons=MappingProxyType({7: "bʿl"}),
    )


def _module_fixture():
    source = normalize_workbook_records(
        (
            WorkbookRecord(
                source_file="01 Synthetic/Worksheet 1.csv",
                source_row=1,
                source_page=7,
                section="Section α",
                root="bʿl",
                headword="bʿl",
                ktu="1.14",
                references="I.2",
                locus="GP",
                room="R1",
                point="",
                depth="",
                disputed="",
                comments="synthetic",
            ),
        )
    )
    index = _index()
    alignments = align_burns_source(source, index)
    module = build_burns_module(source, alignments, index)
    report = build_burns_module_report(source, alignments, index, module)
    return module, report


class ReviewedCucCompatibilityFingerprintTests(unittest.TestCase):
    def test_public_payload_exposes_the_complete_enforced_reviewed_contract(self):
        payload = cuc_index.reviewed_cuc_compatibility_payload()

        self.assertEqual(payload["schema"], EXPECTED_SCHEMA)
        self.assertEqual(payload["repository"], "DT-UCPH/cuc")
        self.assertEqual(payload["commit"], "ad69400f5446e1c8217af01659c7c10ab00c015b")
        self.assertEqual(payload["version"], "0.2.8")
        self.assertEqual(
            payload["manifest_sha256"],
            "717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba",
        )
        self.assertEqual(payload["required_features"], EXPECTED_FEATURES)
        self.assertEqual(payload["node_type_counts"], EXPECTED_COUNTS)
        self.assertEqual(payload["section_types"], EXPECTED_SECTION_TYPES)
        self.assertEqual(payload["section_features"], EXPECTED_SECTION_FEATURES)
        self.assertEqual(
            payload["required_files"],
            {
                name: {"size": item.size, "sha256": item.sha256}
                for name, item in sorted(cuc_index.REVIEWED_CUC_FILES.items())
            },
        )
        self.assertEqual(
            list(payload["required_files"]),
            ["column.tf", "g_cons.tf", "line.tf", "oslots.tf", "otype.tf", "tablet.tf"],
        )

    def test_payload_is_deterministic_mutation_isolated_and_environment_free(self):
        first = cuc_index.reviewed_cuc_compatibility_payload()
        second = cuc_index.reviewed_cuc_compatibility_payload()
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

        first["node_type_counts"]["word"] = -1
        first["required_files"]["otype.tf"]["size"] = -1
        fresh = cuc_index.reviewed_cuc_compatibility_payload()
        self.assertEqual(fresh["node_type_counts"]["word"], 27770)
        self.assertEqual(fresh["required_files"]["otype.tf"]["size"], 531)

        serialized = json.dumps(fresh, sort_keys=True).casefold()
        for forbidden in (
            str(Path.home()).casefold(),
            "timestamp",
            "platform",
            "python_version",
            "environment",
            "machine",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_feature_headers_and_report_project_one_canonical_fingerprint(self):
        module, report = _module_fixture()
        payload = cuc_index.reviewed_cuc_compatibility_payload()
        expected_counts = json.dumps(
            payload["node_type_counts"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        self.assertEqual(report["cuc_compatibility"], payload)
        for metadata in module.metadata.values():
            self.assertEqual(metadata["cucRepository"], payload["repository"])
            self.assertEqual(metadata["cucCommit"], payload["commit"])
            self.assertEqual(metadata["cucVersion"], payload["version"])
            self.assertEqual(metadata["cucManifestSha256"], payload["manifest_sha256"])
            self.assertEqual(metadata["cucCompatibilitySchema"], EXPECTED_SCHEMA)
            self.assertEqual(metadata["cucRequiredFeatures"], "column,g_cons,line,tablet")
            self.assertEqual(metadata["cucNodeTypeCounts"], expected_counts)
            self.assertEqual(metadata["cucSectionTypes"], "tablet,column,line")
            self.assertEqual(metadata["cucSectionFeatures"], "tablet,column,line")

    def test_structural_projection_changes_from_one_central_reviewed_constant(self):
        changed_counts = dict(cuc_index.REVIEWED_CUC_COUNTS)
        changed_counts["word"] += 1
        with patch.object(
            cuc_index,
            "REVIEWED_CUC_COUNTS",
            MappingProxyType(changed_counts),
        ):
            payload = cuc_index.reviewed_cuc_compatibility_payload()
            module, report = _module_fixture()

        expected_counts = json.dumps(
            payload["node_type_counts"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(payload["node_type_counts"]["word"], 27771)
        self.assertEqual(report["cuc_compatibility"]["node_type_counts"]["word"], 27771)
        for metadata in module.metadata.values():
            self.assertEqual(metadata["cucNodeTypeCounts"], expected_counts)


if __name__ == "__main__":
    unittest.main()
