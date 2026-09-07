from __future__ import annotations

import argparse
from pathlib import Path

from .graph import build_tf_data
from .pdf_source import load_pdf_directory
from .report import build_conversion_report
from .source import SourceValidationError, load_csv_directory
from .writer import write_artifact


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize Burns Workbooks as Text-Fabric"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    convert = sub.add_parser("convert")
    convert.add_argument("source", type=Path)
    convert.add_argument("--input-format", choices=("csv", "pdf"), required=True)
    convert.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        source = (
            load_csv_directory(args.source)
            if args.input_format == "csv"
            else load_pdf_directory(args.source)
        )
    except SourceValidationError as exc:
        raise SystemExit(f"source validation failed: {exc}") from exc
    data = build_tf_data(source)
    report = build_conversion_report(
        source,
        data,
        source_format=args.input_format,
    )
    if not write_artifact(data, report, args.output):
        raise SystemExit("Text-Fabric refused the generated dataset")
    print(
        f"converted {len(source.files)} Workbook {args.input_format.upper()} files / "
        f"{len(source.records)} records to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
