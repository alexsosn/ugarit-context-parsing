from __future__ import annotations

import csv
import hashlib
import json
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


def _normalized_tf_files(root: Path) -> tuple[dict[str, str], dict[str, int]]:
    normalized: dict[str, str] = {}
    generated_dates: dict[str, int] = {}
    for path in sorted(root.glob("*.tf")):
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        date_lines = [line for line in lines if line.startswith("@dateWritten=")]
        generated_dates[path.name] = len(date_lines)
        normalized[path.name] = "".join(
            line for line in lines if not line.startswith("@dateWritten=")
        )
    return normalized, generated_dates


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
            source = root / "csv"

            # Create the lexically later worksheet first so deterministic source
            # traversal is exercised instead of accidentally matching creation order.
            _write_csv(
                source / "Zeta" / "Second.csv",
                [
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
                ],
            )
            _write_csv(
                source / "Alpha" / "First.csv",
                [
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
                ],
            )

            source_before = _source_snapshot(source)
            output_a = root / "tf-a"
            output_b = root / "tf-b"
            for output in (output_a, output_b):
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

            self.assertEqual(_source_snapshot(source), source_before)

            tf_a, dates_a = _normalized_tf_files(output_a)
            tf_b, dates_b = _normalized_tf_files(output_b)
            self.assertEqual(set(tf_a), set(tf_b))
            self.assertTrue(tf_a, "real Text-Fabric writer must produce .tf files")
            self.assertEqual(tf_a, tf_b)
            self.assertTrue(all(count == 1 for count in dates_a.values()), dates_a)
            self.assertTrue(all(count == 1 for count in dates_b.values()), dates_b)

            report_a = json.loads(
                (output_a / "conversion-report.json").read_text(encoding="utf-8")
            )
            report_b = json.loads(
                (output_b / "conversion-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report_a, report_b)
            self.assertEqual(report_a["status"], "ok")
            self.assertEqual(report_a["counts"]["records"], 3)

            api_a = Fabric(locations=[str(output_a)], modules=[""], silent="deep").loadAll(
                silent="deep"
            )
            api_b = Fabric(locations=[str(output_b)], modules=[""], silent="deep").loadAll(
                silent="deep"
            )
            self.assertIsNotNone(api_a)
            self.assertIsNotNone(api_b)
            assert api_a is not None and api_b is not None

            self.assertEqual(tuple(api_a.Fall()), tuple(api_b.Fall()))
            self.assertEqual(tuple(api_a.Eall()), tuple(api_b.Eall()))
            self.assertEqual(api_a.F.otype.maxSlot, api_b.F.otype.maxSlot)
            self.assertEqual(api_a.F.otype.maxNode, api_b.F.otype.maxNode)
            max_node = api_a.F.otype.maxNode

            self.assertEqual(
                tuple(api_a.F.otype.v(node) for node in range(1, max_node + 1)),
                tuple(api_b.F.otype.v(node) for node in range(1, max_node + 1)),
            )
            for feature in api_a.Fall():
                with self.subTest(feature=feature):
                    self.assertEqual(
                        tuple(api_a.Fs(feature).v(node) for node in range(1, max_node + 1)),
                        tuple(api_b.Fs(feature).v(node) for node in range(1, max_node + 1)),
                    )

            non_slots = range(api_a.F.otype.maxSlot + 1, max_node + 1)
            self.assertEqual(
                tuple(api_a.T.sectionFromNode(node) for node in non_slots),
                tuple(api_b.T.sectionFromNode(node) for node in non_slots),
            )
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
