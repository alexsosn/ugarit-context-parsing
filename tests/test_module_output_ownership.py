from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from ugarit_context_parsing.cuc_index import reviewed_cuc_compatibility_payload
from ugarit_context_parsing.module import (
    BurnsModuleData,
    FEATURES,
    MODULE_REPORT_SCHEMA,
    REPORT_FILE,
    write_burns_module,
)


EXPECTED_TF = tuple(sorted(f"{feature}.tf" for feature in FEATURES))


def _valid_report() -> dict[str, object]:
    return {
        "schema": MODULE_REPORT_SCHEMA,
        "cuc_compatibility": reviewed_cuc_compatibility_payload(),
        "feature_inventory": sorted(FEATURES),
    }


def _module_data() -> BurnsModuleData:
    return BurnsModuleData(
        node_features={feature: {} for feature in FEATURES},
        metadata={feature: {} for feature in FEATURES},
    )


def _write_prior_module(
    output: Path,
    *,
    missing: str | None = None,
    extra: tuple[str, bytes] | None = None,
    report: object | None = None,
) -> dict[str, bytes]:
    output.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, bytes] = {}
    for name in EXPECTED_TF:
        if name == missing:
            continue
        payload = f"old:{name}\n".encode()
        (output / name).write_bytes(payload)
        snapshot[name] = payload
    if extra is not None:
        name, payload = extra
        (output / name).write_bytes(payload)
        snapshot[name] = payload
    if report is not None:
        payload = (json.dumps(report, sort_keys=True) + "\n").encode()
        (output / REPORT_FILE).write_bytes(payload)
        snapshot[REPORT_FILE] = payload
    return snapshot


def _snapshot(output: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted(output.iterdir(), key=lambda item: item.name)
        if path.is_file()
    }


class _ModuleFabric:
    init_calls = 0
    save_calls = 0
    live_output: Path | None = None
    inject_unknown = False

    def __init__(self, **kwargs):
        type(self).init_calls += 1

    def save(self, **kwargs):
        type(self).save_calls += 1
        stage = Path(kwargs["location"])
        stage.mkdir(parents=True, exist_ok=True)
        for name in EXPECTED_TF:
            (stage / name).write_text(f"new:{name}\n", encoding="utf-8")
        if type(self).inject_unknown:
            assert type(self).live_output is not None
            (type(self).live_output / "burns_custom.tf").write_bytes(b"late-custom")
        return True


class ModuleOutputOwnershipTests(unittest.TestCase):
    def setUp(self):
        _ModuleFabric.init_calls = 0
        _ModuleFabric.save_calls = 0
        _ModuleFabric.live_output = None
        _ModuleFabric.inject_unknown = False

    def _write(self, output: Path) -> bool:
        return write_burns_module(
            _module_data(),
            _valid_report(),
            output,
            fabric_factory=_ModuleFabric,
        )

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_unknown_regular_burns_prefixed_file_is_not_owned_by_prefix(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            before = _write_prior_module(
                output,
                extra=("burns_custom.tf", b"user-local-custom"),
                report=_valid_report(),
            )

            with self.assertRaisesRegex(ValueError, "inventory|unknown|unexpected"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_snapshot(output), before)

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_foreign_tf_file_remains_rejected(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            before = _write_prior_module(
                output,
                extra=("foreign.tf", b"foreign"),
                report=_valid_report(),
            )

            with self.assertRaisesRegex(ValueError, "non-Burns|inventory|foreign|unexpected"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_snapshot(output), before)

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_exact_prior_module_remains_replaceable(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            _write_prior_module(output, report=_valid_report())

            self.assertTrue(self._write(output))

            self.assertEqual(_ModuleFabric.init_calls, 1)
            self.assertEqual(_ModuleFabric.save_calls, 1)
            self.assertEqual(
                {path.name for path in output.glob("*.tf")},
                set(EXPECTED_TF),
            )
            self.assertTrue((output / REPORT_FILE).is_file())

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_exact_tf_inventory_without_report_fails_closed(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            before = _write_prior_module(output)

            with self.assertRaisesRegex(ValueError, "report|ownership|incomplete"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_snapshot(output), before)

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_report_with_missing_reviewed_feature_fails_closed(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            before = _write_prior_module(
                output,
                missing="burns_headwords.tf",
                report=_valid_report(),
            )

            with self.assertRaisesRegex(ValueError, "inventory|missing|incomplete"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_snapshot(output), before)

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_foreign_report_identity_fails_closed(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            foreign_report = _valid_report()
            foreign_report["schema"] = "not-burns"
            before = _write_prior_module(output, report=foreign_report)

            with self.assertRaisesRegex(ValueError, "report|ownership|schema"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 0)
            self.assertEqual(_snapshot(output), before)

    @mock.patch("ugarit_context_parsing.module._validate_module_for_write")
    def test_unknown_file_added_during_staging_is_rejected_without_deletion(self, _validate):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "module"
            before = _write_prior_module(output, report=_valid_report())
            _ModuleFabric.live_output = output
            _ModuleFabric.inject_unknown = True

            with self.assertRaisesRegex(ValueError, "inventory|unknown|unexpected"):
                self._write(output)

            self.assertEqual(_ModuleFabric.init_calls, 1)
            self.assertEqual(_ModuleFabric.save_calls, 1)
            after = _snapshot(output)
            for name, payload in before.items():
                self.assertEqual(after[name], payload)
            self.assertEqual(after["burns_custom.tf"], b"late-custom")


if __name__ == "__main__":
    unittest.main()
