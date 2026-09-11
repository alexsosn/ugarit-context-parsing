from __future__ import annotations

from importlib import metadata
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ugarit_context_parsing.graph import TFData
from ugarit_context_parsing.report import build_conversion_report


class ConversionReportProducerVersionTests(unittest.TestCase):
    @staticmethod
    def _source_and_data():
        source = SimpleNamespace(
            records=(object(),),
            files=("Workbook I/Worksheet 1.csv",),
            tree_sha256="0" * 64,
        )
        data = TFData(
            node_features={
                "otype": {1: "record"},
                "source_file": {1: "Workbook I/Worksheet 1.csv"},
                "source_row": {1: 1},
                "source_page": {1: 1},
                "ktu": {},
                "cuc_tablet": {},
            },
            edge_features={"oslots": {}},
            metadata={},
        )
        return source, data

    def test_report_uses_installed_distribution_version_without_changing_schema(self):
        source, data = self._source_and_data()

        report = build_conversion_report(source, data, source_format="csv")

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["converter"]["name"], "ugarit-context-parsing")
        self.assertEqual(
            report["converter"]["version"],
            metadata.version("ugarit-context-parsing"),
        )

    def test_report_follows_future_installed_producer_version_not_source_constant(self):
        source, data = self._source_and_data()

        with patch.object(metadata, "version", return_value="9.8.7"):
            report = build_conversion_report(source, data, source_format="csv")

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["converter"]["version"], "9.8.7")

    def test_missing_distribution_metadata_fails_instead_of_guessing_version(self):
        source, data = self._source_and_data()

        with (
            patch.object(
                metadata,
                "version",
                side_effect=metadata.PackageNotFoundError("ugarit-context-parsing"),
            ),
            self.assertRaises(metadata.PackageNotFoundError),
        ):
            build_conversion_report(source, data, source_format="csv")


if __name__ == "__main__":
    unittest.main()
