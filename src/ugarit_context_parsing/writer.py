from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Protocol

from .graph import TFData


class _FabricLike(Protocol):
    def save(self, **kwargs) -> bool: ...


_REQUIRED_TF = ("otype.tf", "oslots.tf", "otext.tf")
_REPORT = "conversion-report.json"


def _make_fabric(factory: Callable[..., _FabricLike] | None) -> _FabricLike:
    if factory is None:
        try:
            from tf.fabric import Fabric
        except ImportError as exc:
            raise RuntimeError("Text-Fabric is required to write .tf files") from exc
        factory = Fabric
    return factory(locations=[], modules=[], silent="deep")


def _publish(stage: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    staged_tf = {path.name: path for path in stage.glob("*.tf") if path.is_file()}
    with TemporaryDirectory(prefix=".burns-tf-backup-", dir=output.parent) as backup_dir:
        backup = Path(backup_dir)
        old = [path for path in output.glob("*.tf") if path.is_file()]
        report = output / _REPORT
        if report.is_file():
            old.append(report)
        moved_old: list[tuple[Path, Path]] = []
        installed: list[Path] = []
        try:
            for path in old:
                target = backup / path.name
                path.replace(target)
                moved_old.append((target, path))
            for name, path in staged_tf.items():
                target = output / name
                path.replace(target)
                installed.append(target)
            report_stage = stage / _REPORT
            report_stage.replace(output / _REPORT)
            installed.append(output / _REPORT)
        except Exception:
            for path in installed:
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
    if report.get("status") != "ok":
        raise ValueError("refusing to write artifact with failed conversion report")

    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
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
        missing = [name for name in _REQUIRED_TF if not (stage / name).is_file()]
        if missing:
            raise RuntimeError(
                "Text-Fabric save omitted required files: " + ", ".join(missing)
            )
        (stage / _REPORT).write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _publish(stage, output)
    return True
