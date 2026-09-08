from __future__ import annotations

from .graph import TFData
from .identifiers import normalize_cuc_tablet
from .source import WorkbookSource


def build_conversion_report(
    source: WorkbookSource,
    data: TFData,
    *,
    source_format: str,
) -> dict:
    otype = data.node_features.get("otype", {})
    counts_by_type: dict[str, int] = {}
    for kind in otype.values():
        counts_by_type[kind] = counts_by_type.get(kind, 0) + 1
    slots = range(1, data.max_slot + 1)
    ktu = data.node_features.get("ktu", {})
    cuc = data.node_features.get("cuc_tablet", {})
    checks = {
        "graph_valid": not data.validate(),
        "record_count_matches_source": data.max_slot == len(source.records),
        "source_identity_coverage": all(
            node in data.node_features.get("source_file", {})
            and node in data.node_features.get("source_row", {})
            and node in data.node_features.get("source_page", {})
            for node in slots
        ),
        "cuc_identifier_normalization": all(
            cuc.get(node, "") == normalize_cuc_tablet(str(ktu.get(node, "")))
            for node in slots
        ),
    }
    report = {
        "schema_version": 1,
        "converter": {
            "name": "ugarit-context-parsing",
            "version": "0.2.0",
        },
        "source": {
            "format": source_format,
            "tree_sha256": source.tree_sha256,
            "file_count": len(source.files),
        },
        "counts": {
            "records": data.max_slot,
            "nodes": data.max_node,
            "oslots_edges": sum(
                len(values)
                for values in data.edge_features.get("oslots", {}).values()
            ),
            "worksheets": counts_by_type.get("worksheet", 0),
            "sections": counts_by_type.get("section", 0),
            "entries": counts_by_type.get("entry", 0),
            "cuc_tablet_rows": len(cuc),
            "not_attested_rows": sum(
                1
                for node in slots
                if str(ktu.get(node, "")).startswith("Not attested")
            ),
        },
        "checks": checks,
    }
    report["status"] = "ok" if all(checks.values()) else "failed"
    return report
