from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tf.fabric import Fabric

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.source import WORKBOOK_FIELDS


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORKBOOK_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _source_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _write_determinism_fixture(source: Path, *, later_first: bool) -> None:
    alpha_rows = [
        {
            "source_page": 3,
            "section": "Section α",
            "root": "bʿl",
            "headword": "bʿl",
            "ktu": "1.14",
            "references": "I 1",
            "locus": "GP",
            "room": "1",
            "point": "p1",
            "depth": "surface",
            "disputed": "n",
            "comments": "synthetic Unicode fixture",
        },
        {
            "source_page": 4,
            "section": "Section α",
            "root": "bʿl",
            "headword": "bʿlt",
            "ktu": "KTU 1.16",
            "references": "I 2",
            "locus": "GP",
            "room": "1",
            "point": "",
            "depth": "",
            "disputed": "y",
            "comments": "synthetic second entry",
        },
    ]
    zeta_rows = [
        {
            "source_page": 9,
            "section": "Section β",
            "root": "mlk",
            "headword": "mlk",
            "ktu": "1.15",
            "references": "II 2",
            "locus": "PH",
            "room": "2",
            "point": "p2",
            "depth": "deep",
            "disputed": "n",
            "comments": "synthetic second worksheet",
        }
    ]
    files = [
        (source / "Alpha" / "First.csv", alpha_rows),
        (source / "Zeta" / "Second.csv", zeta_rows),
    ]
    if later_first:
        files.reverse()
    for path, rows in files:
        _write_csv(path, rows)


class RealTextFabricIntegrationTests(unittest.TestCase):
    def test_synthetic_csv_materializes_and_reloads_with_section_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "csv"
            path = source / "Divine Names" / "Names.csv"
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
                    "comments": "synthetic fixture",
                },
                {
                    "source_page": 1,
                    "section": "Section α",
                    "root": "",
                    "headword": "bʿl",
                    "ktu": "1.15",
                    "references": "II 2",
                    "locus": "PH",
                    "room": "2",
                    "point": "",
                    "depth": "",
                    "disputed": "n",
                    "comments": "synthetic fixture two",
                },
            ]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=WORKBOOK_FIELDS)
                writer.writeheader()
                writer.writerows(rows)

            output = root / "tf"
            self.assertEqual(main([
                "convert",
                str(source),
                "--input-format",
                "csv",
                "--output",
                str(output),
            ]), 0)

            for required in ("otype.tf", "oslots.tf", "otext.tf", "conversion-report.json"):
                self.assertTrue((output / required).is_file(), required)
            report = json.loads((output / "conversion-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["counts"]["records"], 2)

            api = Fabric(locations=[str(output)], modules=[""], silent="deep").load(
                "headword ktu cuc_tablet source_file source_row source_page section_source",
                silent="deep",
            )
            self.assertIsNotNone(api)
            assert api is not None
            records = tuple(api.F.otype.s("record"))
            self.assertEqual(records, (1, 2))
            self.assertEqual([api.F.headword.v(node) for node in records], ["bʿl", "bʿl"])
            self.assertEqual([api.F.cuc_tablet.v(node) for node in records], ["KTU 1.14", "KTU 1.15"])
            self.assertEqual(api.F.source_file.v(1), "Divine Names/Names.csv")

            worksheets = tuple(api.F.otype.s("worksheet"))
            self.assertEqual(len(worksheets), 1)
            self.assertEqual(api.T.sectionFromNode(worksheets[0])[0], "Divine Names/Names")

    def test_repeated_synthetic_csv_materialization_is_semantically_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_a = root / "csv-a"
            source_b = root / "csv-b"

            # The two source roots contain identical relative files/bytes, but
            # are created in opposite orders. This proves cache-relevant output
            # is independent of both absolute root spelling and creation order.
            _write_determinism_fixture(source_a, later_first=True)
            _write_determinism_fixture(source_b, later_first=False)
            source_before_a = _source_snapshot(source_a)
            source_before_b = _source_snapshot(source_b)
            self.assertEqual(source_before_a, source_before_b)

            output_a = root / "tf-a"
            output_b = root / "tf-b"
            for source, output in ((source_a, output_a), (source_b, output_b)):
                self.assertEqual(
                    main([
                        "convert",
                        str(source),
                        "--input-format",
                        "csv",
                        "--output",
                        str(output),
                    ]),
                    0,
                )

            self.assertEqual(_source_snapshot(source_a), source_before_a)
            self.assertEqual(_source_snapshot(source_b), source_before_b)
            self.assertEqual(_source_snapshot(source_a), _source_snapshot(source_b))

            # Freeze a third artifact before any comparator load. This avoids a
            # loaded-path cache masking the negative control after mutation.
            output_bad = root / "tf-b-perturbed"
            shutil.copytree(output_b, output_bad)
            cuc_path = output_bad / "cuc_tablet.tf"
            cuc_text = cuc_path.read_text(encoding="utf-8")
            self.assertEqual(cuc_text.count("KTU 1.14"), 1)
            cuc_path.write_text(
                cuc_text.replace("KTU 1.14", "KTU 9.99", 1),
                encoding="utf-8",
            )

            # TDD RED: this private comparator is intentionally absent in this
            # commit. CI must fail here before the helper implementation lands.
            from ugarit_context_parsing._semantic_compare import (
                compare_text_fabric_artifacts,
            )

            self.assertEqual(compare_text_fabric_artifacts(output_a, output_b), ())
            differences = compare_text_fabric_artifacts(output_a, output_bad)
            self.assertIn(
                "normalized Text-Fabric file differs: cuc_tablet.tf",
                differences,
            )
            self.assertIn("node feature differs: cuc_tablet", differences)

            report_a = json.loads(
                (output_a / "conversion-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report_a["status"], "ok")
            self.assertEqual(report_a["counts"]["records"], 3)

            api_a = Fabric(locations=[str(output_a)], modules=[""], silent="deep").loadAll(
                silent="deep"
            )
            self.assertIsNotNone(api_a)
            assert api_a is not None
            self.assertEqual(
                [api_a.T.sectionFromNode(node)[0] for node in api_a.F.otype.s("worksheet")],
                ["Alpha/First", "Zeta/Second"],
            )
            self.assertEqual(len(api_a.F.otype.s("record")), 3)
            self.assertEqual(len(api_a.F.otype.s("worksheet")), 2)
            self.assertEqual(len(api_a.F.otype.s("section")), 2)
            self.assertEqual(len(api_a.F.otype.s("entry")), 3)


if __name__ == "__main__":
    unittest.main()
