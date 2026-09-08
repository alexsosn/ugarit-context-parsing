from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from tf.fabric import Fabric

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.source import WORKBOOK_FIELDS


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


if __name__ == "__main__":
    unittest.main()
