from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .alignment import align_burns_source
from .annotations import BurnsNormalizationError, normalize_workbook_records
from .cuc_index import CucCompatibilityError, build_reviewed_cuc_index
from .graph import build_tf_data
from .module import build_burns_module, build_burns_module_report, write_burns_module
from .pdf_source import load_pdf_directory
from .report import build_conversion_report
from .source import SourceValidationError, load_csv_directory
from .writer import write_artifact


LEGACY_CONVERT_WARNING = (
    "deprecated: 'convert' creates the legacy standalone Burns row-slot corpus; "
    "use 'module' for the CUC-aligned feature module"
)


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source", type=Path)
    parser.add_argument("--input-format", choices=("csv", "pdf"), required=True)
    parser.add_argument("--output", type=Path, required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize Burns Workbooks as a CUC-aligned Text-Fabric feature module"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    module = sub.add_parser(
        "module",
        help="primary CUC-aligned Text-Fabric feature-module materialization",
    )
    _add_source_arguments(module)
    module.add_argument(
        "--cuc",
        type=Path,
        required=True,
        help="exact reviewed CUC 0.2.8 Text-Fabric directory",
    )

    convert = sub.add_parser(
        "convert",
        help="deprecated legacy standalone Burns row-slot corpus materialization",
    )
    _add_source_arguments(convert)
    return parser


def _load_source(args: argparse.Namespace):
    return (
        load_csv_directory(args.source)
        if args.input_format == "csv"
        else load_pdf_directory(args.source)
    )


def _validate_source_output_disjoint(source_root: Path, output: Path) -> None:
    canonical_source = Path(source_root).resolve(strict=False)
    canonical_output = Path(output).resolve(strict=False)
    if (
        canonical_source == canonical_output
        or canonical_source.is_relative_to(canonical_output)
        or canonical_output.is_relative_to(canonical_source)
    ):
        raise SystemExit(
            "source/output paths must be disjoint: "
            f"source={canonical_source}; output={canonical_output}"
        )


def _validated_source_root(args: argparse.Namespace, source) -> Path:
    """Use the loader's canonical root when available without widening its public seam."""
    return Path(getattr(source, "root", args.source))


def _run_module(args: argparse.Namespace) -> int:
    try:
        source = _load_source(args)
    except SourceValidationError as exc:
        raise SystemExit(f"source validation failed: {exc}") from exc

    _validate_source_output_disjoint(_validated_source_root(args, source), args.output)

    try:
        normalized = normalize_workbook_records(source.records)
    except BurnsNormalizationError as exc:
        raise SystemExit(f"Burns normalization failed: {exc}") from exc

    try:
        index = build_reviewed_cuc_index(args.cuc)
    except CucCompatibilityError as exc:
        raise SystemExit(f"CUC validation failed: {exc}") from exc

    alignments = align_burns_source(normalized, index)
    module = build_burns_module(normalized, alignments, index)
    report = build_burns_module_report(normalized, alignments, index, module)
    if not write_burns_module(module, report, args.output):
        raise SystemExit("Text-Fabric refused the generated Burns module")

    print(
        f"materialized {len(source.files)} Workbook {args.input_format.upper()} files / "
        f"{len(normalized.records)} records / {len(normalized.annotations)} annotations "
        f"as a CUC-aligned Burns feature module at {args.output}"
    )
    return 0


def _run_convert(args: argparse.Namespace) -> int:
    print(LEGACY_CONVERT_WARNING, file=sys.stderr)
    try:
        source = _load_source(args)
    except SourceValidationError as exc:
        raise SystemExit(f"source validation failed: {exc}") from exc

    _validate_source_output_disjoint(_validated_source_root(args, source), args.output)

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


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "module":
        return _run_module(args)
    return _run_convert(args)


if __name__ == "__main__":
    raise SystemExit(main())
