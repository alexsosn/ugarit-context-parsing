from __future__ import annotations

import json
from collections import defaultdict
from typing import Iterable

from .alignment import BurnsAlignmentOccurrence
from .annotations import BurnsAnnotation


def _entry(annotation: BurnsAnnotation, occurrence: BurnsAlignmentOccurrence) -> dict[str, object]:
    return {
        "schema": "burns-cuc-occurrence-v1",
        "annotation_id": annotation.annotation_id,
        "occurrence_id": occurrence.occurrence_id,
        "record_ids": list(annotation.record_ids),
        "disposition": occurrence.disposition.value,
        "reason": occurrence.reason.value,
        "confidence": occurrence.confidence.value,
        "anchor_kind": occurrence.anchor_kind.value if occurrence.anchor_kind else None,
        "anchor_nodes": list(occurrence.anchor_nodes),
        "context_line_node": occurrence.context_line_node,
        "worksheet_id": annotation.worksheet_id,
        "workbook_number": annotation.workbook_number,
        "worksheet_number": annotation.worksheet_number,
        "worksheet_role": annotation.worksheet_role.value,
        "section": annotation.section,
        "root": annotation.root,
        "headword": annotation.headword,
        "textual_status": annotation.textual_status.value,
        "semantic_status": annotation.semantic_status.value,
        "interpretive_status": annotation.interpretive_status.value,
    }


def build_module_features(
    aligned_occurrences: Iterable[tuple[BurnsAnnotation, BurnsAlignmentOccurrence]],
) -> dict[str, dict[int, str]]:
    """Build feature-only Burns payloads on existing CUC carrier nodes.

    Unanchored occurrences remain report-only. Span entries are repeated on each
    carrier node but retain their complete ordered span; exact duplicate input is
    collapsed by occurrence identity + anchor tuple.
    """
    by_node: dict[int, dict[tuple[str, tuple[int, ...]], dict[str, object]]] = defaultdict(dict)
    for annotation, occurrence in aligned_occurrences:
        if occurrence.anchor_kind is None or not occurrence.anchor_nodes:
            continue
        entry = _entry(annotation, occurrence)
        key = (occurrence.occurrence_id, occurrence.anchor_nodes)
        for node in occurrence.anchor_nodes:
            if not isinstance(node, int) or node <= 0:
                raise ValueError(f"invalid CUC carrier node: {node!r}")
            previous = by_node[node].get(key)
            if previous is not None and previous != entry:
                raise ValueError("same Burns occurrence identity has conflicting payloads")
            by_node[node][key] = entry

    if not by_node:
        return {}

    feature: dict[int, str] = {}
    for node in sorted(by_node):
        entries = sorted(
            by_node[node].values(),
            key=lambda item: (
                str(item["occurrence_id"]),
                tuple(item["anchor_nodes"]),
                str(item["annotation_id"]),
            ),
        )
        feature[node] = json.dumps(
            entries,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return {"burns_annotations": feature}
