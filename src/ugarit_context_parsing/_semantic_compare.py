from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tf.fabric import Fabric

_REQUIRED_FILES = ("otype.tf", "oslots.tf", "otext.tf", "conversion-report.json")
_DATE_PREFIX = "@dateWritten="


def _freeze(value: Any) -> Any:
    """Normalize TF edge API values into deterministic comparable structures."""
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze(item)) for key, item in value.items()))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _normalized_tf_files(
    root: Path,
    side: str,
    differences: list[str],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not root.is_dir():
        differences.append(f"{side} artifact directory missing")
        return normalized

    for path in sorted(root.glob("*.tf"), key=lambda item: item.name):
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeError):
            differences.append(f"{side} Text-Fabric file unreadable: {path.name}")
            continue
        date_count = sum(line.startswith(_DATE_PREFIX) for line in lines)
        if date_count != 1:
            differences.append(
                f"{side} @dateWritten count for {path.name}: {date_count}"
            )
        normalized[path.name] = "".join(
            line for line in lines if not line.startswith(_DATE_PREFIX)
        )
    return normalized


def _load_report(root: Path, side: str, differences: list[str]) -> Any:
    path = root / "conversion-report.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        differences.append(f"{side} conversion report unreadable")
        return None


def _load_tf(root: Path, side: str, differences: list[str]):
    try:
        api = Fabric(locations=[str(root)], modules=[""], silent="deep").loadAll(
            silent="deep"
        )
    except Exception:
        differences.append(f"{side} Text-Fabric artifact failed to load")
        return None
    if api is None or api is False:
        differences.append(f"{side} Text-Fabric artifact failed to load")
        return None
    return api


def _edge_items(api: Any, feature: str) -> tuple[Any, ...]:
    items = (_freeze(item) for item in api.Es(feature).items())
    return tuple(sorted(items, key=repr))


def compare_text_fabric_artifacts(
    left: str | Path,
    right: str | Path,
) -> tuple[str, ...]:
    """Compare two generated Burns TF artifacts under one execution identity.

    The only ignored persisted field is Text-Fabric's generated ``@dateWritten``
    header. An empty tuple means equality across the complete persisted TF/report
    surface plus loaded nodes, node features, edges, and section navigation.
    """
    left_root = Path(left)
    right_root = Path(right)
    differences: list[str] = []

    for side, root in (("left", left_root), ("right", right_root)):
        for name in _REQUIRED_FILES:
            if not (root / name).is_file():
                differences.append(f"{side} required artifact missing: {name}")

    left_tf = _normalized_tf_files(left_root, "left", differences)
    right_tf = _normalized_tf_files(right_root, "right", differences)
    if set(left_tf) != set(right_tf):
        differences.append("Text-Fabric filename set differs")
    for name in sorted(set(left_tf) & set(right_tf)):
        if left_tf[name] != right_tf[name]:
            differences.append(f"normalized Text-Fabric file differs: {name}")

    left_report = _load_report(left_root, "left", differences)
    right_report = _load_report(right_root, "right", differences)
    if left_report is not None and right_report is not None and left_report != right_report:
        differences.append("conversion report differs")

    # Only attempt semantic loading if both required warp files exist. Missing
    # files have already failed closed above and Fabric diagnostics add no value.
    left_warp = all((left_root / name).is_file() for name in _REQUIRED_FILES[:3])
    right_warp = all((right_root / name).is_file() for name in _REQUIRED_FILES[:3])
    left_api = _load_tf(left_root, "left", differences) if left_warp else None
    right_api = _load_tf(right_root, "right", differences) if right_warp else None
    if left_api is None or right_api is None:
        return tuple(differences)

    left_max_slot = left_api.F.otype.maxSlot
    right_max_slot = right_api.F.otype.maxSlot
    left_max_node = left_api.F.otype.maxNode
    right_max_node = right_api.F.otype.maxNode
    if (left_max_slot, left_max_node) != (right_max_slot, right_max_node):
        differences.append("node bounds differ")

    left_types = tuple(
        left_api.F.otype.v(node) for node in range(1, left_max_node + 1)
    )
    right_types = tuple(
        right_api.F.otype.v(node) for node in range(1, right_max_node + 1)
    )
    if left_types != right_types:
        differences.append("node type sequence differs")

    left_node_features = tuple(sorted(left_api.Fall()))
    right_node_features = tuple(sorted(right_api.Fall()))
    if left_node_features != right_node_features:
        differences.append("node feature inventory differs")
    for feature in sorted(set(left_node_features) & set(right_node_features)):
        left_values = tuple(
            left_api.Fs(feature).v(node) for node in range(1, left_max_node + 1)
        )
        right_values = tuple(
            right_api.Fs(feature).v(node) for node in range(1, right_max_node + 1)
        )
        if left_values != right_values:
            differences.append(f"node feature differs: {feature}")

    left_edge_features = tuple(sorted(left_api.Eall()))
    right_edge_features = tuple(sorted(right_api.Eall()))
    if left_edge_features != right_edge_features:
        differences.append("edge feature inventory differs")
    for feature in sorted(set(left_edge_features) & set(right_edge_features)):
        if _edge_items(left_api, feature) != _edge_items(right_api, feature):
            differences.append(f"edge feature differs: {feature}")

    left_sections = tuple(
        left_api.T.sectionFromNode(node)
        for node in range(left_max_slot + 1, left_max_node + 1)
    )
    right_sections = tuple(
        right_api.T.sectionFromNode(node)
        for node in range(right_max_slot + 1, right_max_node + 1)
    )
    if left_sections != right_sections:
        differences.append("section navigation differs")

    return tuple(differences)
