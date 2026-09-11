from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from ugarit_context_parsing.module import BurnsModuleData, FEATURES, write_burns_module


class _StagedReportSymlinkFabric:
    report_target: Path | None = None

    def __init__(self, **kwargs):
        pass

    def save(self, **kwargs):
        stage = Path(kwargs["location"])
        stage.mkdir(parents=True, exist_ok=True)
        for feature in FEATURES:
            (stage / f"{feature}.tf").write_text(
                f"module:{feature}\n",
                encoding="utf-8",
            )
        assert type(self).report_target is not None
        (stage / "burns-module-report.json").symlink_to(type(self).report_target)
        return True


def _module_data() -> BurnsModuleData:
    return BurnsModuleData(
        node_features={feature: {} for feature in FEATURES},
        metadata={feature: {} for feature in FEATURES},
    )


class OutputRootSymlinkAdversarialTests(unittest.TestCase):
    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_module_rejects_staged_report_symlink_before_write(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "module-output"
            target = root / "outside.json"
            target.write_bytes(b"outside")
            _StagedReportSymlinkFabric.report_target = target

            try:
                with self.assertRaisesRegex(ValueError, "symlink"):
                    write_burns_module(
                        _module_data(),
                        {},
                        output,
                        fabric_factory=_StagedReportSymlinkFabric,
                    )
            finally:
                _StagedReportSymlinkFabric.report_target = None

            self.assertEqual(target.read_bytes(), b"outside")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
