from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from ugarit_context_parsing.graph import TFData
from ugarit_context_parsing.writer import write_artifact


class _SyntheticFabric:
    generation = 1
    saves = 0

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs

    def save(self, **kwargs):
        type(self).saves += 1
        location = Path(kwargs["location"])
        location.mkdir(parents=True, exist_ok=True)
        for name in ("otype.tf", "oslots.tf", "otext.tf", "headword.tf"):
            (location / name).write_text(
                f"generation={type(self).generation};name={name}\n",
                encoding="utf-8",
            )
        return True


def _data() -> TFData:
    return TFData(
        node_features={
            "otype": {1: "record"},
            "headword": {1: "bʿl"},
        },
        edge_features={"oslots": {}},
        metadata={
            "": {"dataset": "synthetic"},
            "otext": {
                "sectionTypes": "",
                "sectionFeatures": "",
                "fmt:text-orig-full": "{headword}",
            },
            "otype": {"valueType": "str"},
            "headword": {"valueType": "str"},
            "oslots": {"valueType": "str"},
        },
    )


def _report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "converter": {
            "name": "ugarit-context-parsing",
            "version": "0.2.0",
        },
        "source": {
            "format": "csv",
            "tree_sha256": "0" * 64,
            "file_count": 1,
        },
        "counts": {
            "records": 1,
            "nodes": 1,
            "oslots_edges": 0,
            "worksheets": 0,
            "sections": 0,
            "entries": 0,
            "cuc_tablet_rows": 0,
            "not_attested_rows": 0,
        },
        "checks": {
            "graph_valid": True,
            "record_count_matches_source": True,
            "source_identity_coverage": True,
            "cuc_identifier_normalization": True,
        },
        "status": "ok",
    }


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_file() and not path.is_symlink()
    }


class LegacyWriterOutputSafetyTests(unittest.TestCase):
    def setUp(self):
        _SyntheticFabric.generation = 1
        _SyntheticFabric.saves = 0

    def test_foreign_tf_corpus_is_rejected_before_fabric_and_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "foreign"
            output.mkdir()
            for name in ("otype.tf", "oslots.tf", "otext.tf", "g_cons.tf"):
                (output / name).write_bytes(f"foreign:{name}".encode("utf-8"))
            before = _snapshot(output)

            with self.assertRaisesRegex(ValueError, "existing.*Text-Fabric|foreign|owned"):
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

            self.assertEqual(_SyntheticFabric.saves, 0)
            self.assertEqual(_snapshot(output), before)

    def test_unknown_tf_is_not_deleted_from_recognized_prior_burns_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "burns"
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)
            )
            (output / "foreign.tf").write_bytes(b"must survive")
            before = _snapshot(output)
            _SyntheticFabric.saves = 0
            _SyntheticFabric.generation = 2

            with self.assertRaisesRegex(ValueError, "foreign|unknown|owned"):
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

            self.assertEqual(_SyntheticFabric.saves, 0)
            self.assertEqual(_snapshot(output), before)

    def test_recognized_prior_burns_artifact_is_replaced_transactionally(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "burns"
            (output.parent / "keep.txt").write_text("outside", encoding="utf-8")
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)
            )
            old_otype = (output / "otype.tf").read_bytes()
            (output / "unrelated.txt").write_text("keep", encoding="utf-8")

            _SyntheticFabric.generation = 2
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)
            )

            self.assertNotEqual((output / "otype.tf").read_bytes(), old_otype)
            self.assertIn(b"generation=2", (output / "otype.tf").read_bytes())
            self.assertEqual((output / "unrelated.txt").read_text(encoding="utf-8"), "keep")
            self.assertEqual((output.parent / "keep.txt").read_text(encoding="utf-8"), "outside")

    def test_mid_publication_failure_restores_prior_burns_artifact_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "burns"
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)
            )
            before = _snapshot(output)
            _SyntheticFabric.generation = 2
            original_replace = Path.replace

            def fail_one_staged_install(path: Path, target: Path):
                if path.parent.name.startswith(".burns-tf-stage-") and path.name == "oslots.tf":
                    raise OSError("synthetic mid-publication failure")
                return original_replace(path, target)

            with mock.patch("pathlib.Path.replace", autospec=True, side_effect=fail_one_staged_install):
                with self.assertRaisesRegex(OSError, "mid-publication"):
                    write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

            self.assertEqual(_snapshot(output), before)

    def test_report_only_and_incomplete_prior_artifacts_are_rejected(self):
        cases = {
            "report-only": (),
            "missing-oslots": ("otype.tf", "otext.tf"),
        }
        for label, tf_names in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "ambiguous"
                output.mkdir()
                (output / "conversion-report.json").write_text(
                    json.dumps(_report()), encoding="utf-8"
                )
                for name in tf_names:
                    (output / name).write_text("old", encoding="utf-8")
                before = _snapshot(output)
                _SyntheticFabric.saves = 0

                with self.assertRaisesRegex(ValueError, "existing|incomplete|owned"):
                    write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

                self.assertEqual(_SyntheticFabric.saves, 0)
                self.assertEqual(_snapshot(output), before)

    def test_invalid_report_does_not_grant_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "ambiguous"
            output.mkdir()
            for name in ("otype.tf", "oslots.tf", "otext.tf"):
                (output / name).write_text("old", encoding="utf-8")
            (output / "conversion-report.json").write_text(
                json.dumps({"schema_version": 1, "status": "ok"}), encoding="utf-8"
            )
            before = _snapshot(output)

            with self.assertRaisesRegex(ValueError, "report|owned"):
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

            self.assertEqual(_SyntheticFabric.saves, 0)
            self.assertEqual(_snapshot(output), before)

    def test_symlinked_tf_candidate_is_rejected_without_moving_link_or_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "burns"
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)
            )
            target = root / "outside.tf"
            target.write_text("outside", encoding="utf-8")
            (output / "headword.tf").unlink()
            (output / "headword.tf").symlink_to(target)
            _SyntheticFabric.saves = 0

            with self.assertRaisesRegex(ValueError, "symlink|owned"):
                write_artifact(_data(), _report(), output, fabric_factory=_SyntheticFabric)

            self.assertEqual(_SyntheticFabric.saves, 0)
            self.assertTrue((output / "headword.tf").is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), "outside")


if __name__ == "__main__":
    unittest.main()
