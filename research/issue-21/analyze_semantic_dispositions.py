#!/usr/bin/env python3
"""Aggregate Burns alignment by dissertation-defined semantic disposition.

This probe exists because raw Workbook rows include positive classifications,
alpha2 no-secure-cultic uses, and beta homographs. Product feature design must
be based on the positive alpha/alpha1 subset, not on all rows mixed together.
Only aggregate counts are printed.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_real_source import (  # noqa: E402
    _find_spans,
    _headword_variants,
    _load_burns,
    _load_cuc,
    _resolve_line_nodes,
    parse_reference_shape,
)
from ugarit_context_parsing.identifiers import normalize_cuc_tablet  # noqa: E402


def semantic_status(section: str) -> str:
    normalized = section.replace("Section", "").strip()
    return {
        "α": "positive_fixed",
        "α1": "probable_cultic",
        "α2": "no_secure_cultic",
        "β": "homograph_excluded",
    }.get(normalized, "unknown")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyze_semantic_dispositions.py CUC_TF_DIR")
    cuc_tf = Path(sys.argv[1]).resolve()
    _rows, annotations, _pdf_counts = _load_burns()
    _api, tablets, lines_exact, lines_by_number, line_words = _load_cuc(cuc_tf)

    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    status_counts: Counter[str] = Counter()
    status_alignment: dict[str, Counter[str]] = defaultdict(Counter)

    positive_spans: dict[int, tuple[int, ...]] = {}
    positive_category: dict[int, str] = {}
    node_to_positive: dict[int, set[int]] = defaultdict(set)

    for index, annotation in enumerate(annotations):
        status = semantic_status(annotation.section)
        status_counts[status] += 1
        matrix[annotation.category][status] += 1

        if annotation.ktu.casefold().startswith("not attested"):
            status_alignment[status]["not_attested"] += 1
            continue
        tablet = normalize_cuc_tablet(annotation.ktu)
        if not tablet:
            status_alignment[status]["ktu_unparsed"] += 1
            continue
        if tablet not in tablets:
            status_alignment[status]["out_of_cuc"] += 1
            continue
        refs = parse_reference_shape(annotation.references)
        if not refs.targets:
            status_alignment[status]["reference_unparsed"] += 1
            continue
        line_nodes, line_ambiguous = _resolve_line_nodes(
            tablet, refs, lines_exact, lines_by_number
        )
        if not line_nodes:
            status_alignment[status][
                "line_unresolved_ambiguous" if line_ambiguous else "line_unresolved"
            ] += 1
            continue
        spans = _find_spans(_headword_variants(annotation.headword), line_nodes, line_words)
        if len(spans) == 1:
            status_alignment[status]["exact_unique"] += 1
            if status in {"positive_fixed", "probable_cultic"}:
                positive_spans[index] = spans[0]
                positive_category[index] = annotation.category
                for node in spans[0]:
                    node_to_positive[node].add(index)
        elif len(spans) > 1:
            status_alignment[status]["exact_multiple"] += 1
        else:
            status_alignment[status]["no_exact_headword_match"] += 1

    positive_pairs: set[tuple[int, int]] = set()
    for ids in node_to_positive.values():
        positive_pairs.update(combinations(sorted(ids), 2))
    nested_pairs = 0
    cross_category_pairs: Counter[str] = Counter()
    for left, right in positive_pairs:
        left_span = set(positive_spans[left])
        right_span = set(positive_spans[right])
        if left_span <= right_span or right_span <= left_span:
            nested_pairs += 1
        left_category = positive_category[left]
        right_category = positive_category[right]
        if left_category != right_category:
            cross_category_pairs[" + ".join(sorted((left_category, right_category)))] += 1

    output = {
        "semantic_status_counts": dict(sorted(status_counts.items())),
        "category_by_semantic_status": {
            category: dict(sorted(counts.items()))
            for category, counts in sorted(matrix.items())
        },
        "alignment_by_semantic_status": {
            status: dict(sorted(counts.items()))
            for status, counts in sorted(status_alignment.items())
        },
        "positive_exact_multiplicity_lower_bound": {
            "unique_exact_positive_annotations": len(positive_spans),
            "cuc_words_with_positive_annotation": len(node_to_positive),
            "cuc_words_with_multiple_positive_annotations": sum(
                1 for ids in node_to_positive.values() if len(ids) > 1
            ),
            "max_positive_annotations_on_one_word": max(
                (len(ids) for ids in node_to_positive.values()), default=0
            ),
            "overlapping_positive_annotation_pairs": len(positive_pairs),
            "nested_positive_annotation_pairs": nested_pairs,
            "cross_category_positive_overlap_pairs": dict(cross_category_pairs.most_common()),
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
