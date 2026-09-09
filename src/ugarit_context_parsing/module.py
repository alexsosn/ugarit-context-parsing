from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Callable, Mapping, Protocol

from .alignment import (
    BurnsAnchorKind,
    BurnsAnnotationAlignment,
    build_alignment_report,
)
from .annotations import BurnsAnnotation, BurnsSourceRecord, NormalizedBurnsSource
from .cuc_index import (
    REVIEWED_CUC_COMMIT,
    REVIEWED_CUC_MANIFEST_SHA256,
    REVIEWED_CUC_REPOSITORY,
    REVIEWED_CUC_VERSION,
    ReviewedCucIndex,
)

MODULE_SCHEMA = "burns-tf-module-v1"
NODE_ANNOTATION_SCHEMA = "burns-node-annotation-v1"
MODULE_REPORT_SCHEMA = "burns-tf-module-report-v1"
REPORT_FILE = "burns-module-report.json"

FEATURES = (
    "burns_annotations",
    "burns_annotation_ids",
    "burns_semantic_statuses",
    "burns_worksheet_roles",
    "burns_sections",
    "burns_headwords",
)
_EXPECTED_TF_FILES = frozenset(f"{feature}.tf" for feature in FEATURES)

_DESCRIPTIONS = {
    "burns_annotations": (
        "Authoritative canonical JSON array of Burns annotation occurrences "
        "aligned to this existing CUC node"
    ),
    "burns_annotation_ids": "Canonical JSON array of Burns semantic annotation IDs",
    "burns_semantic_statuses": "Canonical JSON array of Burns semantic statuses",
    "burns_worksheet_roles": "Canonical JSON array of Burns worksheet roles",
    "burns_sections": "Canonical JSON array of Burns section labels",
    "burns_headwords": "Canonical JSON array of Burns source headwords",
}

_PROJECTION_FIELDS = {
    "burns_annotation_ids": "annotation_id",
    "burns_semantic_statuses": "semantic_status",
    "burns_worksheet_roles": "worksheet_role",
    "burns_sections": "section",
    "burns_headwords": "headword",
}


class _FabricLike(Protocol):
    def save(self, **kwargs) -> bool: ...


@dataclass(frozen=True)
class BurnsModuleData:
    node_features: Mapping[str, Mapping[int, str]]
    metadata: Mapping[str, Mapping[str, str]]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _reviewed_compatibility_payload() -> dict[str, str]:
    return {
        "repository": REVIEWED_CUC_REPOSITORY,
        "commit": REVIEWED_CUC_COMMIT,
        "version": REVIEWED_CUC_VERSION,
        "manifest_sha256": REVIEWED_CUC_MANIFEST_SHA256,
    }


def _compatibility_payload(index: ReviewedCucIndex) -> dict[str, str]:
    compatibility = index.compatibility
    if compatibility is None:
        raise ValueError("Burns TF module requires a reviewed CUC compatibility identity")

    expected = _reviewed_compatibility_payload()
    actual = {
        "repository": compatibility.repository,
        "commit": compatibility.commit,
        "version": compatibility.version,
        "manifest_sha256": compatibility.manifest_sha256,
    }
    if actual != expected:
        raise ValueError(
            "Burns TF module requires the exact reviewed CUC identity: "
            f"expected {expected!r}; got {actual!r}"
        )
    return actual


def _record_payload(record: BurnsSourceRecord) -> dict[str, object]:
    return {
        "record_id": record.record_id,
        "source_file": record.source_file,
        "source_row": record.source_row,
        "source_page": record.source_page,
        "locus": record.locus,
        "room": record.room,
        "point": record.point,
        "depth": record.depth,
        "disputed": record.disputed,
        "comments": record.comments,
    }


def _target_payload(target) -> dict[str, object]:
    return {
        "tablet": target.tablet,
        "column": target.column,
        "line": target.line,
    }


def _occurrence_payload(
    annotation: BurnsAnnotation,
    alignment: BurnsAnnotationAlignment,
    records_by_id: Mapping[str, BurnsSourceRecord],
    occurrence,
) -> dict[str, object]:
    source_records = []
    for record_id in annotation.record_ids:
        record = records_by_id.get(record_id)
        if record is None:
            raise ValueError(
                f"annotation {annotation.annotation_id} references missing source record {record_id}"
            )
        source_records.append(_record_payload(record))

    return {
        "schema": NODE_ANNOTATION_SCHEMA,
        "annotation_id": annotation.annotation_id,
        "occurrence_id": occurrence.occurrence_id,
        "target_ordinal": occurrence.target_ordinal,
        "record_ids": list(annotation.record_ids),
        "source_records": source_records,
        "worksheet_id": annotation.worksheet_id,
        "workbook_number": annotation.workbook_number,
        "workbook_label": annotation.workbook_label,
        "worksheet_number": annotation.worksheet_number,
        "worksheet_role": annotation.worksheet_role.value,
        "section": annotation.section,
        "root": annotation.root,
        "headword": annotation.headword,
        "ktu": annotation.ktu,
        "references": annotation.references,
        "textual_status": annotation.textual_status.value,
        "semantic_status": annotation.semantic_status.value,
        "interpretive_status": annotation.interpretive_status.value,
        "annotation_disposition": alignment.disposition.value,
        "annotation_reason": alignment.reason.value,
        "disposition": occurrence.disposition.value,
        "reason": occurrence.reason.value,
        "confidence": occurrence.confidence.value,
        "anchor_kind": occurrence.anchor_kind.value if occurrence.anchor_kind else None,
        "anchor_nodes": list(occurrence.anchor_nodes),
        "context_line_node": occurrence.context_line_node,
        "target": _target_payload(occurrence.target),
        "candidate_line_nodes": list(occurrence.candidate_line_nodes),
        "candidate_spans": [list(span) for span in occurrence.candidate_spans],
    }


def _payload_identity(payload: Mapping[str, object]) -> tuple[object, ...]:
    anchor_nodes = payload.get("anchor_nodes")
    if not isinstance(anchor_nodes, list) or not all(isinstance(node, int) for node in anchor_nodes):
        raise ValueError("Burns node annotation has invalid anchor_nodes")
    return (
        payload.get("annotation_id"),
        payload.get("occurrence_id"),
        payload.get("anchor_kind"),
        tuple(anchor_nodes),
    )


def burns_node_annotations(value: str) -> tuple[dict[str, object], ...]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("burns_annotations must contain valid JSON") from exc
    if not isinstance(payload, list):
        raise ValueError("burns_annotations must be a JSON array")

    result: list[dict[str, object]] = []
    previous_identity: tuple[object, ...] | None = None
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("burns_annotations array members must be objects")
        if item.get("schema") != NODE_ANNOTATION_SCHEMA:
            raise ValueError("unsupported Burns node annotation schema")
        identity = _payload_identity(item)
        if previous_identity is not None and identity <= previous_identity:
            raise ValueError("burns_annotations entries are not in strict canonical identity order")
        previous_identity = identity
        result.append(dict(item))

    if _canonical_json(result) != value:
        raise ValueError("burns_annotations value is not canonical JSON")
    return tuple(result)


def _project_payloads(
    payloads: tuple[dict[str, object], ...],
) -> dict[str, str]:
    return {
        feature: _canonical_json(
            sorted({str(item[payload_field]) for item in payloads})
        )
        for feature, payload_field in _PROJECTION_FIELDS.items()
    }


def _expected_feature_metadata(feature: str) -> dict[str, str]:
    compatibility = _reviewed_compatibility_payload()
    return {
        "valueType": "str",
        "module": "Burns",
        "moduleSchema": MODULE_SCHEMA,
        "cucRepository": compatibility["repository"],
        "cucCommit": compatibility["commit"],
        "cucVersion": compatibility["version"],
        "cucManifestSha256": compatibility["manifest_sha256"],
        "description": _DESCRIPTIONS[feature],
    }


def _immutable_nested(
    values: Mapping[str, Mapping[int, str]],
) -> Mapping[str, Mapping[int, str]]:
    return MappingProxyType(
        {
            feature: MappingProxyType(dict(sorted(node_values.items())))
            for feature, node_values in sorted(values.items())
        }
    )


def _immutable_metadata(
    values: Mapping[str, Mapping[str, str]],
) -> Mapping[str, Mapping[str, str]]:
    return MappingProxyType(
        {
            feature: MappingProxyType(dict(sorted(metadata.items())))
            for feature, metadata in sorted(values.items())
        }
    )


def build_burns_module(
    source: NormalizedBurnsSource,
    alignments: tuple[BurnsAnnotationAlignment, ...],
    index: ReviewedCucIndex,
) -> BurnsModuleData:
    _compatibility_payload(index)

    # Reuse #26 as the integrity gate. This rejects missing/extra/forged
    # alignments and proves every normalized source record is partitioned
    # exactly once before any node payload is emitted.
    build_alignment_report(source, alignments, index)

    alignments_by_id = {alignment.annotation_id: alignment for alignment in alignments}
    records_by_id = {record.record_id: record for record in source.records}

    per_node: dict[int, dict[tuple[object, ...], tuple[str, dict[str, object]]]] = {}
    ordered_annotations = sorted(
        source.annotations,
        key=lambda item: (item.worksheet_id, item.first_source_row, item.annotation_id),
    )
    for annotation in ordered_annotations:
        alignment = alignments_by_id[annotation.annotation_id]
        for occurrence in sorted(alignment.occurrences, key=lambda item: item.target_ordinal):
            if occurrence.anchor_kind is None or not occurrence.anchor_nodes:
                continue
            if occurrence.anchor_kind is not BurnsAnchorKind.WORD_SPAN and len(occurrence.anchor_nodes) != 1:
                raise ValueError("non-span Burns occurrence must select exactly one CUC node")

            payload = _occurrence_payload(annotation, alignment, records_by_id, occurrence)
            identity = _payload_identity(payload)
            canonical = _canonical_json(payload)
            for node in occurrence.anchor_nodes:
                entries = per_node.setdefault(node, {})
                previous = entries.get(identity)
                if previous is not None:
                    if previous[0] != canonical:
                        raise ValueError(
                            "conflicting Burns payloads share one stable occurrence identity"
                        )
                    continue
                entries[identity] = (canonical, payload)

    authoritative: dict[int, str] = {}
    projections: dict[str, dict[int, str]] = {
        feature: {} for feature in FEATURES if feature != "burns_annotations"
    }
    for node in sorted(per_node):
        payloads = [
            item[1]
            for _, item in sorted(per_node[node].items(), key=lambda pair: pair[0])
        ]
        value = _canonical_json(payloads)
        authoritative[node] = value

        # Derive every convenience feature from the authoritative serialized
        # value, keeping burns_annotations as the sole source of truth.
        parsed = burns_node_annotations(value)
        for feature, projected_value in _project_payloads(parsed).items():
            projections[feature][node] = projected_value

    node_features: dict[str, Mapping[int, str]] = {
        "burns_annotations": authoritative,
        **projections,
    }
    metadata = {
        feature: _expected_feature_metadata(feature)
        for feature in FEATURES
    }
    return BurnsModuleData(
        node_features=_immutable_nested(node_features),
        metadata=_immutable_metadata(metadata),
    )


def _plain_module(module: BurnsModuleData) -> tuple[dict[str, dict[int, str]], dict[str, dict[str, str]]]:
    node_features = {
        feature: dict(values) for feature, values in module.node_features.items()
    }
    metadata = {
        feature: dict(values) for feature, values in module.metadata.items()
    }
    return node_features, metadata


def build_burns_module_report(
    source: NormalizedBurnsSource,
    alignments: tuple[BurnsAnnotationAlignment, ...],
    index: ReviewedCucIndex,
    module: BurnsModuleData,
) -> dict[str, object]:
    expected = build_burns_module(source, alignments, index)
    if _plain_module(module) != _plain_module(expected):
        raise ValueError("Burns TF module does not match deterministic source/alignment data")

    alignment_report = build_alignment_report(source, alignments, index)
    compatibility = _compatibility_payload(index)
    disposition_counts = dict(
        sorted(Counter(alignment.disposition.value for alignment in alignments).items())
    )
    selected_occurrences = [
        occurrence
        for alignment in alignments
        for occurrence in alignment.occurrences
        if occurrence.anchor_kind is not None and occurrence.anchor_nodes
    ]
    anchor_kind_counts = dict(
        sorted(Counter(occurrence.anchor_kind.value for occurrence in selected_occurrences).items())
    )
    return {
        "schema": MODULE_REPORT_SCHEMA,
        "cuc_compatibility": compatibility,
        "counts": {
            "records": len(source.records),
            "annotations": len(source.annotations),
            "alignment_dispositions": disposition_counts,
            "selected_occurrences": len(selected_occurrences),
            "anchor_kinds": anchor_kind_counts,
            "touched_nodes": len(module.node_features["burns_annotations"]),
        },
        "feature_inventory": sorted(FEATURES),
        "alignment": alignment_report,
    }


def _make_fabric(factory: Callable[..., _FabricLike] | None) -> _FabricLike:
    if factory is None:
        try:
            from tf.fabric import Fabric
        except ImportError as exc:
            raise RuntimeError("Text-Fabric is required to write Burns module features") from exc
        factory = Fabric
    return factory(locations=[], modules=[], silent="deep")


def _validate_module_for_write(module: BurnsModuleData, report: Mapping[str, object]) -> None:
    if set(module.node_features) != set(FEATURES):
        raise ValueError("Burns TF module node-feature inventory is not the reviewed v1 inventory")
    if set(module.metadata) != set(FEATURES):
        raise ValueError("Burns TF module metadata inventory is not the reviewed v1 inventory")

    authoritative_nodes = set(module.node_features["burns_annotations"])
    parsed_by_node: dict[int, tuple[dict[str, object], ...]] = {}
    for node, value in module.node_features["burns_annotations"].items():
        parsed_by_node[node] = burns_node_annotations(value)

    for feature in FEATURES:
        if set(module.node_features[feature]) != authoritative_nodes:
            raise ValueError(f"Burns projection node coverage differs for {feature}")
        if dict(module.metadata[feature]) != _expected_feature_metadata(feature):
            raise ValueError(f"invalid Burns TF metadata for {feature}")

    for node, parsed in parsed_by_node.items():
        expected_projections = _project_payloads(parsed)
        for feature, expected_value in expected_projections.items():
            actual_value = module.node_features[feature][node]
            if actual_value != expected_value:
                raise ValueError(
                    f"Burns projection {feature} differs from authoritative burns_annotations "
                    f"on node {node}"
                )

    if report.get("schema") != MODULE_REPORT_SCHEMA:
        raise ValueError("refusing to write invalid Burns module report schema")
    if report.get("feature_inventory") != sorted(FEATURES):
        raise ValueError("Burns module report feature inventory does not match module")
    if report.get("cuc_compatibility") != _reviewed_compatibility_payload():
        raise ValueError("Burns module report compatibility is not the exact reviewed CUC identity")


def _publish(stage: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    old_owned = sorted(
        [path for path in output.glob("burns_*.tf") if path.is_file()]
        + ([output / REPORT_FILE] if (output / REPORT_FILE).is_file() else []),
        key=lambda path: path.name,
    )

    with TemporaryDirectory(prefix=".burns-module-backup-", dir=output.parent) as backup_dir:
        backup = Path(backup_dir)
        moved_old: list[tuple[Path, Path]] = []
        installed: list[Path] = []
        try:
            for path in old_owned:
                saved = backup / path.name
                path.replace(saved)
                moved_old.append((saved, path))

            for name in sorted(_EXPECTED_TF_FILES | {REPORT_FILE}):
                staged = stage / name
                target = output / name
                staged.replace(target)
                installed.append(target)
        except Exception:
            for path in reversed(installed):
                if path.exists():
                    path.unlink()
            for saved, original in reversed(moved_old):
                if saved.exists():
                    saved.replace(original)
            raise


def write_burns_module(
    module: BurnsModuleData,
    report: dict[str, object],
    output_dir: str | Path,
    *,
    fabric_factory: Callable[..., _FabricLike] | None = None,
) -> bool:
    _validate_module_for_write(module, report)

    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not output.is_dir():
        raise ValueError(f"Burns module output path is not a directory: {output}")
    if output.is_dir():
        foreign_tf = sorted(
            path.name
            for path in output.glob("*.tf")
            if path.is_file() and not path.name.startswith("burns_")
        )
        if foreign_tf:
            raise ValueError(
                "refusing to publish Burns module into directory containing non-Burns TF files: "
                + ", ".join(foreign_tf)
            )

    fabric = _make_fabric(fabric_factory)
    with TemporaryDirectory(prefix=".burns-module-stage-", dir=output.parent) as stage_dir:
        stage = Path(stage_dir)
        node_features, metadata = _plain_module(module)
        ok = bool(
            fabric.save(
                nodeFeatures=node_features,
                edgeFeatures={},
                metaData=metadata,
                location=str(stage),
                module="",
                silent="deep",
            )
        )
        if not ok:
            return False

        staged_tf = frozenset(
            path.name for path in stage.glob("*.tf") if path.is_file()
        )
        if staged_tf != _EXPECTED_TF_FILES:
            missing = sorted(_EXPECTED_TF_FILES - staged_tf)
            extra = sorted(staged_tf - _EXPECTED_TF_FILES)
            details = []
            if missing:
                details.append("missing=" + ",".join(missing))
            if extra:
                details.append("extra=" + ",".join(extra))
            raise RuntimeError(
                "Text-Fabric Burns module stage has unexpected feature inventory: "
                + "; ".join(details)
            )

        (stage / REPORT_FILE).write_text(
            _canonical_json(report) + "\n",
            encoding="utf-8",
        )
        _publish(stage, output)
    return True
