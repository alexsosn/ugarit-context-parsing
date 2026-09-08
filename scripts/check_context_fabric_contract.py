#!/usr/bin/env python3
"""Pinned downstream Context-Fabric/cfabric-mcp compatibility contract."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from ugarit_context_parsing.cli import main
from ugarit_context_parsing.source import WORKBOOK_FIELDS


_REQUIRED_ARTIFACTS = (
    "otype.tf",
    "oslots.tf",
    "otext.tf",
    "conversion-report.json",
)


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

        # TDD RED: installation and real materialization above must succeed before
        # the downstream consumer assertions are implemented.
        raise NotImplementedError("Context-Fabric consumer assertions not implemented")


if __name__ == "__main__":
    main_contract()
