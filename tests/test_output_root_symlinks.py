from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from ugarit_context_parsing.graph import TFData
from ugarit_context_parsing.module import BurnsModuleData, FEATURES, write_burns_module
from ugarit_context_parsing.writer import write_artifact


class _LegacyFabric:
    init_calls = 0
    save_calls = 0
    substitute_output: Path | None = None
    substitute_target: Path | None = None

    def __init__(self, **kwargs):
        type(self).init_calls += 1

    def save(self, **kwargs):
        type(self).save_calls += 1
        stage = Path(kwargs["location"])
        stage.mkdir(parents=True, exist_ok=True)
        for name in ("otype.tf", "oslots.tf", "otext.tf", "headword.tf"):
            (stage / name).write_text(f"legacy:{name}\n", encoding="utf-8")
        if type(self).substitute_output is not None:
            assert type(self).substitute_target is not None
            type(self).substitute_output.symlink_to(
                type(self).substitute_target,
                target_is_directory=True,
            )
        return True


class _ModuleFabric:
    init_calls = 0
    save_calls = 0
    substitute_output: Path | None = None
    substitute_target: Path | None = None
    staged_symlink_target: Path | None = None

    def __init__(self, **kwargs):
        type(self).init_calls += 1

    def save(self, **kwargs):
        type(self).save_calls += 1
        stage = Path(kwargs["location"])
        stage.mkdir(parents=True, exist_ok=True)
        expected = [f"{feature}.tf" for feature in FEATURES]
        for name in expected:
            path = stage / name
            if name == "burns_annotations.tf" and type(self).staged_symlink_target is not None:
                path.symlink_to(type(self).staged_symlink_target)
            else:
                path.write_text(f"module:{name}\n", encoding="utf-8")
        if type(self).substitute_output is not None:
            assert type(self).substitute_target is not None
            type(self).substitute_output.symlink_to(
                type(self).substitute_target,
                target_is_directory=True,
            )
        return True


def _legacy_data() -> TFData:
    return TFData(
        node_features={"otype": {1: "record"}, "headword": {1: "synthetic"}},
        edge_features={"oslots": {}},
        metadata={
            "": {"dataset": "synthetic"},
            "otext": {"sectionTypes": "", "sectionFeatures": ""},
            "otype": {"valueType": "str"},
            "headword": {"valueType": "str"},
            "oslots": {"valueType": "str"},
        },
    )


def _legacy_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "converter": {"name": "ugarit-context-parsing", "version": "0.2.0"},
        "source": {"format": "csv", "tree_sha256": "0" * 64, "file_count": 1},
        "counts": {"records": 1},
        "checks": {"graph_valid": True},
        "status": "ok",
    }


def _module_data() -> BurnsModuleData:
    return BurnsModuleData(
        node_features={feature: {} for feature in FEATURES},
        metadata={feature: {} for feature in FEATURES},
    )


def _directory_symlink(link: Path, target: Path, testcase: unittest.TestCase) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        testcase.skipTest(f"symlinks unavailable: {exc}")


class OutputRootSymlinkTests(unittest.TestCase):
    def setUp(self):
        _LegacyFabric.init_calls = 0
        _LegacyFabric.save_calls = 0
        _LegacyFabric.substitute_output = None
        _LegacyFabric.substitute_target = None
        _ModuleFabric.init_calls = 0
        _ModuleFabric.save_calls = 0
        _ModuleFabric.substitute_output = None
        _ModuleFabric.substitute_target = None
        _ModuleFabric.staged_symlink_target = None

    def test_legacy_rejects_directory_symlink_output_before_fabric(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real-target"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_bytes(b"keep")
            output = root / "output-link"
            _directory_symlink(output, target, self)

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_artifact(
                    _legacy_data(),
                    _legacy_report(),
                    output,
                    fabric_factory=_LegacyFabric,
                )

            self.assertEqual(_LegacyFabric.init_calls, 0)
            self.assertEqual(_LegacyFabric.save_calls, 0)
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(sorted(path.name for path in target.iterdir()), ["keep.txt"])

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_directory_symlink_output_before_fabric(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real-target"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_bytes(b"keep")
            output = root / "output-link"
            _directory_symlink(output, target, self)

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_ModuleFabric.save_calls, 0)
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(sorted(path.name for path in target.iterdir()), ["keep.txt"])

    def test_legacy_rejects_dangling_output_symlink_before_fabric(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "dangling-output"
            _directory_symlink(output, root / "missing-target", self)
            self.assertTrue(output.is_symlink())

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_artifact(
                    _legacy_data(),
                    _legacy_report(),
                    output,
                    fabric_factory=_LegacyFabric,
                )

            self.assertEqual(_LegacyFabric.init_calls, 0)
            self.assertEqual(_LegacyFabric.save_calls, 0)
            self.assertTrue(output.is_symlink())

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_dangling_output_symlink_before_fabric(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "dangling-output"
            _directory_symlink(output, root / "missing-target", self)
            self.assertTrue(output.is_symlink())

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_ModuleFabric.save_calls, 0)
            self.assertTrue(output.is_symlink())

    def test_legacy_allows_real_leaf_below_symlinked_ancestor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            _directory_symlink(linked_parent, real_parent, self)
            output = linked_parent / "legacy-output"
            self.assertFalse(output.is_symlink())

            self.assertTrue(
                write_artifact(
                    _legacy_data(),
                    _legacy_report(),
                    output,
                    fabric_factory=_LegacyFabric,
                )
            )
            self.assertTrue((real_parent / "legacy-output" / "otype.tf").is_file())

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_allows_real_leaf_below_symlinked_ancestor(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_parent = root / "real-parent"
            real_parent.mkdir()
            linked_parent = root / "linked-parent"
            _directory_symlink(linked_parent, real_parent, self)
            output = linked_parent / "module-output"
            self.assertFalse(output.is_symlink())

            self.assertTrue(
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )
            )
            self.assertTrue(
                (real_parent / "module-output" / "burns_annotations.tf").is_file()
            )

    def test_legacy_rechecks_output_leaf_after_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "legacy-output"
            target = root / "external-target"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_bytes(b"keep")
            _LegacyFabric.substitute_output = output
            _LegacyFabric.substitute_target = target

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_artifact(
                    _legacy_data(),
                    _legacy_report(),
                    output,
                    fabric_factory=_LegacyFabric,
                )

            self.assertEqual(_LegacyFabric.save_calls, 1)
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(sorted(path.name for path in target.iterdir()), ["keep.txt"])

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rechecks_output_leaf_after_staging(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "module-output"
            target = root / "external-target"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_bytes(b"keep")
            _ModuleFabric.substitute_output = output
            _ModuleFabric.substitute_target = target

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertEqual(_ModuleFabric.save_calls, 1)
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(sorted(path.name for path in target.iterdir()), ["keep.txt"])

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_existing_owned_feature_symlink_before_fabric(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "module-output"
            output.mkdir()
            target = root / "outside.tf"
            target.write_bytes(b"outside")
            (output / "burns_annotations.tf").symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(target.read_bytes(), b"outside")
            self.assertTrue((output / "burns_annotations.tf").is_symlink())

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_existing_report_symlink_before_fabric(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "module-output"
            output.mkdir()
            target = root / "outside.json"
            target.write_text("outside", encoding="utf-8")
            (output / "burns-module-report.json").symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "outside")
            self.assertTrue((output / "burns-module-report.json").is_symlink())

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_staged_feature_symlink_before_publication(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "module-output"
            target = root / "outside.tf"
            target.write_bytes(b"outside")
            _ModuleFabric.staged_symlink_target = target

            with self.assertRaisesRegex(ValueError, "symlink"):
                write_burns_module(
                    _module_data(),
                    {},
                    output,
                    fabric_factory=_ModuleFabric,
                )

            self.assertFalse(output.exists())
            self.assertEqual(target.read_bytes(), b"outside")


if __name__ == "__main__":
    unittest.main()
