from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .identifiers import normalize_cuc_tablet
from .source import WorkbookSource

INT_FEATURES = {"source_page", "source_row"}


@dataclass
class TFData:
    node_features: dict[str, dict[int, str | int]]
    edge_features: dict[str, dict[int, set[int]]]
    metadata: dict[str, dict[str, str]]

    @property
    def max_slot(self) -> int:
        return max(
            (n for n, kind in self.node_features.get("otype", {}).items() if kind == "record"),
            default=0,
        )

    @property
    def max_node(self) -> int:
        return max(self.node_features.get("otype", {}), default=0)

    def validate(self) -> list[str]:
        otype = self.node_features.get("otype", {})
        if not otype:
            return ["missing otype"]
        errors: list[str] = []
        max_slot = self.max_slot
        max_node = self.max_node
        if set(otype) != set(range(1, max_node + 1)):
            errors.append("otype node ids are not contiguous from 1")
        if any(otype.get(n) != "record" for n in range(1, max_slot + 1)):
            errors.append("record slots are not the first contiguous nodes")
        if any(otype.get(n) == "record" for n in range(max_slot + 1, max_node + 1)):
            errors.append("record slot found after non-slot nodes")
        by_type: dict[str, list[int]] = {}
        for node, kind in otype.items():
            if kind != "record":
                by_type.setdefault(kind, []).append(node)
        for kind, nodes in by_type.items():
            nodes.sort()
            if nodes != list(range(nodes[0], nodes[-1] + 1)):
                errors.append(
                    f"non-slot node type {kind} does not occupy one contiguous node-id range"
                )
        oslots = self.edge_features.get("oslots", {})
        if set(oslots) != set(range(max_slot + 1, max_node + 1)):
            errors.append("oslots does not map every non-slot node exactly once")
        if any(not slots for slots in oslots.values()):
            errors.append("oslots contains empty support for non-slot node")
        if any(
            not 1 <= slot <= max_slot
            for slots in oslots.values()
            for slot in slots
        ):
            errors.append("oslots points outside slot range")
        return errors


def _set_feature(
    features: dict[str, dict[int, str | int]],
    name: str,
    node: int,
    value: str | int,
) -> None:
    if value != "":
        features.setdefault(name, {})[node] = value


def _occurrence_label(base: str, seen: dict[str, int], fallback: str) -> str:
    label = base.strip() or fallback
    seen[label] = seen.get(label, 0) + 1
    return label if seen[label] == 1 else f"{label}~{seen[label]}"


def build_tf_data(source: WorkbookSource) -> TFData:
    records = source.records
    features: dict[str, dict[int, str | int]] = {
        name: {}
        for name in (
            "otype",
            "source_file",
            "source_row",
            "source_page",
            "section_source",
            "root",
            "headword",
            "ktu",
            "cuc_tablet",
            "references",
            "locus",
            "room",
            "point",
            "depth",
            "disputed",
            "comments",
            "language",
            "worksheet",
            "section",
            "entry",
        )
    }
    for node, record in enumerate(records, start=1):
        features["otype"][node] = "record"
        _set_feature(features, "source_file", node, record.source_file)
        _set_feature(features, "source_row", node, record.source_row)
        _set_feature(features, "source_page", node, record.source_page)
        _set_feature(features, "section_source", node, record.section)
        for name in (
            "root",
            "headword",
            "ktu",
            "references",
            "locus",
            "room",
            "point",
            "depth",
            "disputed",
            "comments",
        ):
            _set_feature(features, name, node, getattr(record, name))
        _set_feature(features, "language", node, "Ugaritic")
        canonical = normalize_cuc_tablet(record.ktu)
        if canonical:
            _set_feature(features, "cuc_tablet", node, canonical)

    worksheet_specs: list[tuple[str, list[int]]] = []
    section_specs: list[tuple[str, list[int]]] = []
    entry_specs: list[tuple[str, list[int]]] = []

    current_file = None
    worksheet_slots: list[int] = []
    current_section_key = None
    section_slots: list[int] = []
    current_entry_key = None
    entry_slots: list[int] = []
    section_seen_by_file: dict[str, dict[str, int]] = {}
    entry_seen_by_section: dict[tuple[str, str], dict[str, int]] = {}
    section_label = ""
    entry_label = ""

    def flush_entry() -> None:
        nonlocal entry_slots
        if entry_slots:
            entry_specs.append((entry_label, entry_slots))
            entry_slots = []

    def flush_section() -> None:
        nonlocal section_slots
        flush_entry()
        if section_slots:
            section_specs.append((section_label, section_slots))
            section_slots = []

    def flush_worksheet() -> None:
        nonlocal worksheet_slots
        flush_section()
        if worksheet_slots and current_file is not None:
            worksheet_label = PurePosixPath(current_file).with_suffix("").as_posix()
            worksheet_specs.append((worksheet_label, worksheet_slots))
            worksheet_slots = []

    for slot, record in enumerate(records, start=1):
        if record.source_file != current_file:
            if current_file is not None:
                flush_worksheet()
            current_file = record.source_file
            current_section_key = None
            current_entry_key = None

        raw_section = record.section
        section_key = (record.source_file, raw_section)
        if section_key != current_section_key:
            if current_section_key is not None:
                flush_section()
            seen = section_seen_by_file.setdefault(record.source_file, {})
            section_label = _occurrence_label(raw_section, seen, "(unsectioned)")
            current_section_key = section_key
            current_entry_key = None

        entry_key = (record.source_file, section_label, record.root, record.headword)
        if entry_key != current_entry_key:
            if current_entry_key is not None:
                flush_entry()
            seen = entry_seen_by_section.setdefault((record.source_file, section_label), {})
            base = record.headword.strip() or record.root.strip()
            entry_label = _occurrence_label(base, seen, "(entry)")
            current_entry_key = entry_key

        worksheet_slots.append(slot)
        section_slots.append(slot)
        entry_slots.append(slot)

    if current_file is not None:
        flush_worksheet()

    oslots: dict[int, set[int]] = {}
    next_node = len(records) + 1
    for kind, feature_name, specs in (
        ("worksheet", "worksheet", worksheet_specs),
        ("section", "section", section_specs),
        ("entry", "entry", entry_specs),
    ):
        for label, slots in specs:
            node = next_node
            next_node += 1
            features["otype"][node] = kind
            features[feature_name][node] = label
            oslots[node] = set(slots)

    metadata: dict[str, dict[str, str]] = {
        "": {
            "dataset": "Burns-Workbooks-TF",
            "datasetName": "Burns Ugaritic cultic-vocabulary Workbooks",
            "source": "Burns, Duncan Coe (2003), Contents, texts and contexts",
            "sourceUrl": "https://etheses.whiterose.ac.uk/id/eprint/15038/",
            "sourceLicence": "CC BY-NC-ND 2.5",
            "cucCompatibility": "KTU tablet identifiers and Ugaritic Unicode conventions only",
            "writtenBy": "ugarit-context-parsing",
            "version": "0.1",
        },
        "otext": {
            "sectionTypes": "worksheet,section,entry",
            "sectionFeatures": "worksheet,section,entry",
            "fmt:text-orig-full": "{headword}",
        },
    }
    descriptions = {
        "source_file": "relative source CSV/PDF path",
        "source_row": "1-based data row within the source worksheet",
        "source_page": "1-based page number in the source PDF",
        "section_source": "literal Burns section label",
        "cuc_tablet": "CUC-compatible canonical KTU tablet identifier",
        "language": "language of the Workbook record",
    }
    for name in features:
        metadata[name] = {
            "valueType": "int" if name in INT_FEATURES else "str",
            "description": descriptions.get(name, f"Burns Workbook feature {name}"),
        }
    metadata["oslots"] = {
        "valueType": "str",
        "description": "Text-Fabric warp edge to record slots",
    }
    data = TFData(features, {"oslots": oslots}, metadata)
    errors = data.validate()
    if errors:
        raise ValueError("invalid generated Text-Fabric graph: " + "; ".join(errors))
    return data
