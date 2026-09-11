from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ugarit_context_parsing.graph import TFData
from ugarit_context_parsing.writer import write_artifact


class _AdversarialFabric:
    saves = 0
    mutate_output: Path | None = None
    extra_stage_file = False

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs

    def save(self, **kwargs):
        type(self).saves += 1
        stage = Path(kwargs["location"])
        stage.mkdir(parents=True, exist_ok=True)
        for name in ("otype.tf", "oslots.tf", "otext.tf", "headword.tf"):
            (stage / name).write_text(f"new:{name}\n", encoding="utf-8")
        if type(self).extra_stage_file:
            (stage / "foreign.tf").write_text("unexpected stage file\n", encoding="utf-8")
        if type(self).mutate_output is not None:
            target = type(self).mutate_output
            target.mkdir(parents=True, exist_ok=True)
            (target / "otype.tf").write_text("concurrent foreign otype\n", encoding="utf-8")
        return True


def _data(*, extra_feature: bool = False) -> TFData:
    node_features: dict[str, dict[int, str]] = {
        "otype": {1: "record"},
        "headword": {1: "bʿl"},
    }
    metadata = {
        "": {"dataset": "synthetic"},
        "otext": {"sectionTypes": "", "sectionFeatures": ""},
        "otype": {"valueType": "str"},
        "headword": {"valueType": "str"},
        "oslots": {"valueType": "str"},
    }
    if extra_feature:
        node_features["g_cons"] = {1: "foreign-looking"}
        metadata["g_cons"] = {"valueType": "str"}
    return TFData(
        node_features=node_features,
        edge_features={"oslots": {}},
        metadata=metadata,
    )


def _report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "converter": {"name": "ugarit-context-parsing", "version": "0.2.0"},
        "source": {"format": "csv", "tree_sha256": "0" * 64, "file_count": 1},
        "counts": {"records": 1},
        "checks": {"graph_valid": True},
        "status": "ok",
    }


class LegacyWriterOutputSafetyAdversarialTests(unittest.TestCase):
    def setUp(self):
        _AdversarialFabric.saves = 0
        _AdversarialFabric.mutate_output = None
        _AdversarialFabric.extra_stage_file = False

    def test_caller_supplied_feature_name_cannot_expand_existing_output_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "burns"
            self.assertTrue(
                write_artifact(_data(), _report(), output, fabric_factory=_AdversarialFabric)
            )
            foreign = output / "g_cons.tf"
            foreign.write_bytes(b"foreign g_cons sentinel")
            _AdversarialFabric.saves = 0

            with self.assertRaisesRegex(ValueError, "foreign|unknown|owned"):
                write_artifact(
                    _data(extra_feature=True),
                    _report(),
                    output,
                    fabric_factory=_AdversarialFabric,
                )

            self.assertEqual(_AdversarialFabric.saves, 0)
            self.assertEqual(foreign.read_bytes(), b"foreign g_cons sentinel")

    def test_output_is_revalidated_after_staging_before_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "target"
            _AdversarialFabric.mutate_output = output

            with self.assertRaisesRegex(ValueError, "existing|foreign|owned"):
                write_artifact(_data(), _report(), output, fabric_factory=_AdversarialFabric)

            self.assertEqual(_AdversarialFabric.saves, 1)
            self.assertEqual(
                (output / "otype.tf").read_text(encoding="utf-8"),
                "concurrent foreign otype\n",
            )
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["otype.tf"])

    def test_unexpected_staged_tf_file_is_rejected_before_output_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "target"
            _AdversarialFabric.extra_stage_file = True

            with self.assertRaisesRegex(ValueError, "staged|unexpected|foreign"):
                write_artifact(_data(), _report(), output, fabric_factory=_AdversarialFabric)

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
