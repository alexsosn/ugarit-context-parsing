#!/usr/bin/env python3
"""Real Context-Fabric/cfabric-mcp contract for CUC + Burns module composition."""

from __future__ import annotations

import argparse
import tempfile
from collections import Counter
from pathlib import Path

from ugarit_context_parsing.alignment import BurnsAnchorKind, align_burns_source
from ugarit_context_parsing.annotations import normalize_workbook_records
from ugarit_context_parsing.cuc_index import build_reviewed_cuc_index
from ugarit_context_parsing.module import (
    FEATURES,
    REPORT_FILE,
    build_burns_module,
    build_burns_module_report,
    burns_node_annotations,
    write_burns_module,
)
from ugarit_context_parsing.source import WorkbookRecord


def _choose_unique_word(index):
    """Pick one public CUC word that resolves uniquely inside its exact line."""
    for (tablet, column, line), line_node in sorted(index.line_nodes.items()):
        words = index.line_words[line_node]
        values = tuple(index.word_g_cons[word] for word in words)
        for word, value in zip(words, values, strict=True):
            if not value or any(character.isspace() for character in value):
                continue
            if value.endswith(("*", "†", "!", "?")):
                continue
            if Counter(values)[value] != 1:
                continue
            return tablet, column, line, line_node, word, value
    raise AssertionError("reviewed CUC has no suitable unique synthetic-contract word")


def _synthetic_source(*, tablet: str, column: str, line: int, headword: str):
    if not tablet.startswith("KTU "):
        raise AssertionError(f"unexpected reviewed CUC tablet label: {tablet!r}")
    record = WorkbookRecord(
        source_file="01 Synthetic/Worksheet 1.csv",
        source_row=1,
        source_page=1,
        section="Section synthetic",
        root="",
        headword=headword,
        ktu=tablet.removeprefix("KTU "),
        references=f"{column}.{line}",
        locus="SYN",
        room="1",
        point="p1",
        depth="synthetic",
        disputed="",
        comments="synthetic Context-Fabric module composition contract",
    )
    return normalize_workbook_records((record,))


def _type_counts(info) -> dict[str, int]:
    return {item["type"]: int(item["count"]) for item in info.node_types}


def _assert_feature_only_inventory(output: Path) -> None:
    expected = {f"{feature}.tf" for feature in FEATURES} | {REPORT_FILE}
    actual = {path.name for path in output.iterdir() if path.is_file()}
    if actual != expected:
        raise AssertionError(
            f"Burns module inventory differs: expected {sorted(expected)!r}, got {sorted(actual)!r}"
        )
    forbidden = {"otype.tf", "oslots.tf", "otext.tf", "g_cons.tf", "tablet.tf", "column.tf", "line.tf"}
    leaked = sorted(forbidden & actual)
    if leaked:
        raise AssertionError("Burns module copied CUC-owned features: " + ", ".join(leaked))


def run_contract(cuc_dir: str | Path) -> None:
    from cfabric_mcp import tools
    from cfabric_mcp.corpus_manager import corpus_manager

    cuc = Path(cuc_dir).resolve()
    index = build_reviewed_cuc_index(cuc)
    tablet, column, line, line_node, word_node, headword = _choose_unique_word(index)
    source = _synthetic_source(
        tablet=tablet,
        column=column,
        line=line,
        headword=headword,
    )
    alignments = align_burns_source(source, index)
    if len(alignments) != 1 or len(alignments[0].occurrences) != 1:
        raise AssertionError("synthetic Burns source did not produce exactly one occurrence")
    occurrence = alignments[0].occurrences[0]
    if occurrence.anchor_kind is not BurnsAnchorKind.WORD_SPAN:
        raise AssertionError(f"expected unique word-span anchor, got {occurrence.anchor_kind!r}")
    if occurrence.anchor_nodes != (word_node,):
        raise AssertionError(
            f"alignment selected {occurrence.anchor_nodes!r}, expected public CUC word {(word_node,)!r}"
        )

    module = build_burns_module(source, alignments, index)
    report = build_burns_module_report(source, alignments, index, module)

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "burns-module"
        if not write_burns_module(module, report, output):
            raise AssertionError("Text-Fabric refused to write the synthetic Burns module")
        _assert_feature_only_inventory(output)

        # Establish the exact base structure through the same public MCP manager.
        base_info = corpus_manager.load(str(cuc), name="cuc-base")
        base_api = corpus_manager.get_api("cuc-base")
        base_type_vector = tuple(
            base_api.F.otype.v(node) for node in range(1, base_info.max_node + 1)
        )
        base_line_words = tuple(base_api.L.d(line_node, otype="word"))

        # Required #28 boundary: one logical corpus, two ordered locations.
        composed_info = corpus_manager.load(
            [str(cuc), str(output)],
            name="cuc-with-burns",
        )
        composed_cf, composed_api = corpus_manager.get("cuc-with-burns")

        if tuple(Path(path).resolve() for path in composed_cf.locations) != (cuc, output.resolve()):
            raise AssertionError(
                f"consumer did not preserve ordered locations: {composed_cf.locations!r}"
            )
        if composed_info.max_slot != base_info.max_slot:
            raise AssertionError("Burns module changed the CUC maximum slot")
        if composed_info.max_node != base_info.max_node:
            raise AssertionError("Burns module changed the CUC maximum node")
        if _type_counts(composed_info) != _type_counts(base_info):
            raise AssertionError("Burns module changed CUC node-type counts")
        if tuple(
            composed_api.F.otype.v(node) for node in range(1, composed_info.max_node + 1)
        ) != base_type_vector:
            raise AssertionError("Burns module changed the CUC node-type vector")
        if tuple(composed_api.L.d(line_node, otype="word")) != base_line_words:
            raise AssertionError("Burns module changed CUC line navigation")

        missing = sorted(set(FEATURES) - set(composed_info.node_features))
        if missing:
            raise AssertionError("cfabric-mcp omitted Burns features: " + ", ".join(missing))

        raw = composed_api.Fs("burns_annotations", warn=False).v(word_node)
        if not raw:
            raise AssertionError("composed API cannot access Burns annotations on selected CUC word")
        payloads = burns_node_annotations(raw)
        if len(payloads) != 1 or payloads[0]["annotation_id"] != source.annotations[0].annotation_id:
            raise AssertionError("composed Burns payload does not match the synthetic source")
        if payloads[0]["anchor_nodes"] != [word_node]:
            raise AssertionError("composed Burns payload lost its exact CUC word anchor")

        # Exercise the actual MCP tool layer, not only the underlying API.
        result = tools.search(
            "word burns_annotations~burns-node-annotation-v1",
            corpus="cuc-with-burns",
            limit=20,
        )
        if "error" in result:
            raise AssertionError(f"MCP Burns-feature search failed: {result!r}")
        returned_nodes = {
            int(node["node"])
            for row in result.get("results", [])
            for node in row
        }
        if word_node not in returned_nodes:
            raise AssertionError(
                f"MCP Burns-feature search did not return selected CUC word {word_node}: {result!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cuc_dir", help="Exact reviewed CUC Text-Fabric directory")
    args = parser.parse_args()
    run_contract(args.cuc_dir)


if __name__ == "__main__":
    main()
