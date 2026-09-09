#!/usr/bin/env python3
"""Pinned downstream Context-Fabric/cfabric-mcp compatibility contract."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path
from typing import Any

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.source import WORKBOOK_FIELDS


_REQUIRED_ARTIFACTS = (
    "otype.tf",
    "oslots.tf",
    "otext.tf",
    "conversion-report.json",
)
_REQUIRED_NODE_FEATURES = {
    "headword",
    "ktu",
    "cuc_tablet",
    "language",
    "source_file",
    "source_row",
    "source_page",
}
_EXPECTED_NODE_COUNTS = {
    "record": 2,
    "worksheet": 1,
    "section": 1,
    "entry": 2,
}


def _row(*, headword: str, ktu: str, references: str, room: str) -> dict[str, object]:
    return {
        "source_page": 1,
        "section": "Section synthetic",
        "root": "",
        "headword": headword,
        "ktu": ktu,
        "references": references,
        "locus": "GP",
        "room": room,
        "point": "",
        "depth": "",
        "disputed": "n",
        "comments": "synthetic consumer contract",
    }


def _write_source(root: Path) -> None:
    path = root / "Synthetic" / "Worksheet.csv"
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORKBOOK_FIELDS)
        writer.writeheader()
        writer.writerows(
            [
                _row(headword="bʿl", ktu="1.14", references="I 1", room="1"),
                _row(headword="mlk", ktu="1.16", references="II 2", room="2"),
            ]
        )


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _feature_values(api: Any, feature: str, nodes: tuple[int, ...]) -> list[Any]:
    feature_api = api.Fs(feature, warn=False)
    if not feature_api:
        raise AssertionError(f"Context-Fabric did not load required feature {feature!r}")
    return [feature_api.v(node) for node in nodes]


def _assert_consumer_contract(output: Path) -> None:
    from cfabric_mcp.corpus_manager import CorpusManager

    manager = CorpusManager()
    info = manager.load(str(output), name="burns-synthetic")
    api = manager.get_api()

    _require_equal(manager.list_corpora(), ["burns-synthetic"], "loaded corpus names")
    _require_equal(manager.current, "burns-synthetic", "current corpus")
    _require_equal(info.slot_type, "record", "slot type")
    _require_equal(info.max_slot, 2, "maximum slot")
    _require_equal(
        info.section_types,
        ["worksheet", "section", "entry"],
        "section type hierarchy",
    )

    node_counts = {item["type"]: item["count"] for item in info.node_types}
    _require_equal(node_counts, _EXPECTED_NODE_COUNTS, "node type counts")

    missing_features = sorted(_REQUIRED_NODE_FEATURES.difference(info.node_features))
    if missing_features:
        raise AssertionError(
            "Context-Fabric corpus inventory omitted required node features: "
            + ", ".join(missing_features)
        )

    records = tuple(int(node) for node in api.F.otype.s("record"))
    _require_equal(records, (1, 2), "record nodes")
    _require_equal(_feature_values(api, "headword", records), ["bʿl", "mlk"], "headwords")
    _require_equal(_feature_values(api, "ktu", records), ["1.14", "1.16"], "KTU values")
    _require_equal(
        _feature_values(api, "cuc_tablet", records),
        ["KTU 1.14", "KTU 1.16"],
        "CUC tablet identifiers",
    )
    _require_equal(
        _feature_values(api, "language", records),
        ["Ugaritic", "Ugaritic"],
        "language values",
    )
    _require_equal(
        _feature_values(api, "source_file", records),
        ["Synthetic/Worksheet.csv", "Synthetic/Worksheet.csv"],
        "source file provenance",
    )
    _require_equal(_feature_values(api, "source_row", records), [1, 2], "source rows")
    _require_equal(_feature_values(api, "source_page", records), [1, 1], "source pages")

    worksheets = tuple(int(node) for node in api.F.otype.s("worksheet"))
    _require_equal(len(worksheets), 1, "worksheet node count")
    section = api.T.sectionFromNode(worksheets[0])
    if not section:
        raise AssertionError("Context-Fabric did not resolve worksheet section navigation")
    _require_equal(section[0], "Synthetic/Worksheet", "worksheet section reference")

    _require_equal([api.T.text(node) for node in records], ["bʿl", "mlk"], "record text")


def main_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source"
        output = root / "tf"
        _write_source(source)

        result = main(
            [
                "convert",
                str(source),
                "--input-format",
                "csv",
                "--output",
                str(output),
            ]
        )
        if result != 0:
            raise AssertionError(f"materializer returned {result}")
        missing = [name for name in _REQUIRED_ARTIFACTS if not (output / name).is_file()]
        if missing:
            raise AssertionError(f"materializer omitted required artifacts: {missing}")

        _assert_consumer_contract(output)


if __name__ == "__main__":
    main_contract()
