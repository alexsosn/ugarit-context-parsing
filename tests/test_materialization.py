from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.graph import build_tf_data
from ugarit_context_parsing.report import build_conversion_report
from ugarit_context_parsing.source import WORKBOOK_FIELDS, load_csv_directory
from ugarit_context_parsing.writer import write_artifact


class _FakeFabric:
    should_succeed = True
    saves: list[dict] = []

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs

    def save(self, **kwargs):
        type(self).saves.append(kwargs)
        if not type(self).should_succeed:
            return False
        location = Path(kwargs["location"])
        location.mkdir(parents=True, exist_ok=True)
        for name in ("otype.tf", "oslots.tf", "otext.tf", "headword.tf"):
            (location / name).write_text(f"synthetic {name}\n", encoding="utf-8")
        return True


class MaterializationTests(unittest.TestCase):
    def setUp(self):
        _FakeFabric.should_succeed = True
        _FakeFabric.saves = []

    @staticmethod
    def _source(root: Path):
        path = root / "Workbook I" / "Worksheet 1.csv"
        path.parent.mkdir(parents=True)
        rows = [
            {
                "source_page": 1,
                "section": "Section α",
                "root": "",
                "headword": "bʿl",
                "ktu": "1.14",
                "references": "I 1",
                "locus": "GP",
                "room": "1",
                "point": "",
                "depth": "",
                "disputed": "n",
                "comments": "synthetic",
            },
            {
                "source_page": 2,
                "section": "Section β",
                "root": "",
                "headword": "špš",
                "ktu": "Not attested",
                "references": "synthetic note",
                "locus": "",
                "room": "",
                "point": "",
                "depth": "",
                "disputed": "",
                "comments": "synthetic two",
            },
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=WORKBOOK_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return load_csv_directory(root)

    def test_report_contains_deterministic_counts_checks_and_no_absolute_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._source(Path(tmp))
            data = build_tf_data(source)
            first = build_conversion_report(source, data, source_format="csv")
            second = build_conversion_report(source, data, source_format="csv")

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], 1)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["source"]["format"], "csv")
        self.assertEqual(first["source"]["file_count"], 1)
        self.assertRegex(first["source"]["tree_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["counts"]["records"], 2)
        self.assertEqual(first["counts"]["worksheets"], 1)
        self.assertEqual(first["counts"]["cuc_tablet_rows"], 1)
        self.assertEqual(first["counts"]["not_attested_rows"], 1)
        self.assertTrue(all(first["checks"].values()))
        payload = json.dumps(first, ensure_ascii=False)
        self.assertNotIn(str(source.root), payload)
        self.assertNotIn("synthetic note", payload)
        self.assertNotIn("synthetic two", payload)

    def test_successful_publication_replaces_tf_set_and_report_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root / "source")
            data = build_tf_data(source)
            report = build_conversion_report(source, data, source_format="csv")
            output = root / "tf"
            output.mkdir()
            (output / "stale.tf").write_text("old", encoding="utf-8")
            (output / "unrelated.txt").write_text("keep", encoding="utf-8")

            ok = write_artifact(data, report, output, fabric_factory=_FakeFabric)

            self.assertTrue(ok)
            self.assertFalse((output / "stale.tf").exists())
            self.assertEqual((output / "unrelated.txt").read_text(encoding="utf-8"), "keep")
            self.assertEqual(
                json.loads((output / "conversion-report.json").read_text(encoding="utf-8")),
                report,
            )
            for required in ("otype.tf", "oslots.tf", "otext.tf"):
                self.assertTrue((output / required).is_file())

    def test_failed_fabric_save_leaves_previous_artifact_untouched(self):
        _FakeFabric.should_succeed = False
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root / "source")
            data = build_tf_data(source)
            report = build_conversion_report(source, data, source_format="csv")
            output = root / "tf"
            output.mkdir()
            (output / "otype.tf").write_text("old corpus", encoding="utf-8")
            (output / "conversion-report.json").write_text('{"old":true}\n', encoding="utf-8")

            ok = write_artifact(data, report, output, fabric_factory=_FakeFabric)

            self.assertFalse(ok)
            self.assertEqual((output / "otype.tf").read_text(encoding="utf-8"), "old corpus")
            self.assertEqual(
                json.loads((output / "conversion-report.json").read_text(encoding="utf-8")),
                {"old": True},
            )

    @mock.patch("ugarit_context_parsing.cli.write_artifact")
    def test_csv_cli_uses_shared_graph_and_report_path(self, write_artifact_mock):
        write_artifact_mock.return_value = True
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._source(root / "source")
            output = root / "tf"
            result = main([
                "convert",
                str(source.root),
                "--input-format",
                "csv",
                "--output",
                str(output),
            ])

        self.assertEqual(result, 0)
        self.assertEqual(write_artifact_mock.call_count, 1)
        data, report, target = write_artifact_mock.call_args.args[:3]
        self.assertEqual(data.max_slot, 2)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["source"]["format"], "csv")
        self.assertEqual(target, output)


if __name__ == "__main__":
    unittest.main()
