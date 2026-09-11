from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Protocol

from .graph import TFData
from .publication import prepare_output_root


class _FabricLike(Protocol):
    def save(self, **kwargs) -> bool: ...


_REQUIRED_TF = frozenset(("otype.tf", "oslots.tf", "otext.tf"))
_LEGACY_TF_NAMES = frozenset(
    {
        "otype.tf",
        "source_file.tf",
        "source_row.tf",
        "source_page.tf",
        "section_source.tf",
        "root.tf",
        "headword.tf",
        "ktu.tf",
        "cuc_tablet.tf",
        "references.tf",
        "locus.tf",
        "room.tf",
        "point.tf",
        "depth.tf",
        "disputed.tf",
        "comments.tf",
        "language.tf",
        "worksheet.tf",
        "section.tf",
        "entry.tf",
        "oslots.tf",
        "otext.tf",
    }
)
_REPORT = "conversion-report.json"


def _make_fabric(factory: Callable[..., _FabricLike] | None) -> _FabricLike:
    if factory is None:
        try:
            from tf.fabric import Fabric
        except ImportError as exc:
            raise RuntimeError("Text-Fabric is required to write .tf files") from exc
        factory = Fabric
    return factory(locations=[], modules=[], silent="deep")


def _requested_tf_names(data: TFData) -> frozenset[str]:
    return frozenset(
        {f"{name}.tf" for name in data.node_features}
        | {f"{name}.tf" for name in data.edge_features}
        | {"otext.tf"}
    )


def _validate_requested_tf_inventory(data: TFData) -> None:
    unexpected = sorted(_requested_tf_names(data) - _LEGACY_TF_NAMES)
    if unexpected:
        raise ValueError(
            "legacy Burns data requests foreign or unknown Text-Fabric features: "
            + ", ".join(unexpected)
        )


def _read_existing_burns_report(path: Path) -> dict[str, object]:
    if path.is_symlink():
        raise ValueError("existing Burns conversion report is a symlink; ownership is ambiguous")
    if not path.is_file():
        raise ValueError("existing Text-Fabric output has no Burns conversion report")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("existing conversion report does not prove Burns output ownership") from exc
    if not isinstance(payload, dict):
        raise ValueError("existing conversion report does not prove Burns output ownership")

    converter = payload.get("converter")
    source = payload.get("source")
    checks = payload.get("checks")
    tree_sha256 = source.get("tree_sha256") if isinstance(source, dict) else None
    file_count = source.get("file_count") if isinstance(source, dict) else None
    if (
        type(payload.get("schema_version")) is not int
        or payload.get("schema_version") != 1
        or payload.get("status") != "ok"
        or not isinstance(converter, dict)
        or converter.get("name") != "ugarit-context-parsing"
        or not isinstance(converter.get("version"), str)
        or not converter["version"].strip()
        or not isinstance(source, dict)
        or source.get("format") not in {"csv", "pdf"}
        or not isinstance(tree_sha256, str)
        or len(tree_sha256) != 64
        or any(char not in "0123456789abcdef" for char in tree_sha256)
        or type(file_count) is not int
        or file_count < 1
        or not isinstance(payload.get("counts"), dict)
        or not isinstance(checks, dict)
        or not checks
        or any(value is not True for value in checks.values())
    ):
        raise ValueError("existing conversion report does not prove Burns output ownership")
    return payload


def _validate_existing_output(output: Path) -> tuple[Path, ...]:
    output = prepare_output_root(output, label="legacy Text-Fabric")
    if not output.exists():
        return ()

    tf_entries = sorted(output.glob("*.tf"), key=lambda path: path.name)
    report = output / _REPORT
    report_exists = report.exists() or report.is_symlink()
    if not tf_entries and not report_exists:
        return ()
    if not tf_entries:
        raise ValueError(
            "existing conversion report is not accompanied by a complete Burns Text-Fabric artifact"
        )
    if not report_exists:
        raise ValueError("existing Text-Fabric output is not proven to be owned by Burns")

    _read_existing_burns_report(report)

    for path in tf_entries:
        if path.is_symlink():
            raise ValueError(
                f"existing Text-Fabric candidate is a symlink; ownership is ambiguous: {path.name}"
            )
        if not path.is_file():
            raise ValueError(
                f"existing Text-Fabric candidate is not a regular file: {path.name}"
            )

    names = {path.name for path in tf_entries}
    foreign = sorted(names - _LEGACY_TF_NAMES)
    if foreign:
        raise ValueError(
            "refusing to replace foreign or unknown Text-Fabric files: "
            + ", ".join(foreign)
        )
    missing = sorted(_REQUIRED_TF - names)
    if missing:
        raise ValueError(
            "existing Burns Text-Fabric artifact is incomplete; missing: "
            + ", ".join(missing)
        )
    return tuple(tf_entries) + (report,)


def _validate_staged_tf(stage: Path) -> dict[str, Path]:
    entries = sorted(stage.glob("*.tf"), key=lambda path: path.name)
    staged: dict[str, Path] = {}
    for path in entries:
        if path.is_symlink():
            raise ValueError(f"staged Text-Fabric file is a symlink: {path.name}")
        if not path.is_file():
            raise ValueError(f"staged Text-Fabric entry is not a regular file: {path.name}")
        staged[path.name] = path

    unexpected = sorted(set(staged) - _LEGACY_TF_NAMES)
    if unexpected:
        raise ValueError(
            "staged Text-Fabric output contains unexpected or foreign files: "
            + ", ".join(unexpected)
        )
    missing = sorted(_REQUIRED_TF - set(staged))
    if missing:
        raise RuntimeError(
            "Text-Fabric save omitted required files: " + ", ".join(missing)
        )
    return staged


def _publish(
    staged_tf: dict[str, Path],
    report_stage: Path,
    output: Path,
    old_owned: tuple[Path, ...],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".burns-tf-backup-", dir=output.parent) as backup_dir:
        backup = Path(backup_dir)
        moved_old: list[tuple[Path, Path]] = []
        installed: list[Path] = []
        try:
            for path in old_owned:
                target = backup / path.name
                path.replace(target)
                moved_old.append((target, path))
            for name, path in sorted(staged_tf.items()):
                target = output / name
                path.replace(target)
                installed.append(target)
            report_stage.replace(output / _REPORT)
            installed.append(output / _REPORT)
        except Exception:
            for path in reversed(installed):
                if path.exists():
                    path.unlink()
            for saved, original in reversed(moved_old):
                if saved.exists():
                    saved.replace(original)
            raise


def write_artifact(
    data: TFData,
    report: dict,
    output_dir: str | Path,
    *,
    fabric_factory: Callable[..., _FabricLike] | None = None,
) -> bool:
    failures = data.validate()
    if failures:
        raise ValueError(
            "refusing to write invalid Text-Fabric data: " + "; ".join(failures)
        )
    _validate_requested_tf_inventory(data)
    if report.get("status") != "ok":
        raise ValueError("refusing to write artifact with failed conversion report")

    output = Path(output_dir)
    _validate_existing_output(output)
    fabric = _make_fabric(fabric_factory)
    with TemporaryDirectory(prefix=".burns-tf-stage-", dir=output.parent) as stage_dir:
        stage = Path(stage_dir)
        ok = bool(
            fabric.save(
                nodeFeatures=data.node_features,
                edgeFeatures=data.edge_features,
                metaData=data.metadata,
                location=str(stage),
                module="",
                silent="deep",
            )
        )
        if not ok:
            return False
        staged_tf = _validate_staged_tf(stage)
        report_stage = stage / _REPORT
        report_stage.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        old_owned = _validate_existing_output(output)
        _publish(staged_tf, report_stage, output, old_owned)
    return True
