from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sources import WORKBOOKS, ensure
from ugarit_context_parsing.annotations import (
    BurnsSemanticStatus,
    BurnsTextualStatus,
    normalize_workbook_records,
)
from ugarit_context_parsing.cuc_index import build_reviewed_cuc_index
from ugarit_context_parsing.pdf_source import load_pdf_directory
from ugarit_context_parsing.references import BurnsReferenceStatus, parse_burns_reference

EDITORIAL_MARKERS = "*†!?"
POSITIVE_STATUSES = {
    BurnsSemanticStatus.POSITIVE_FIXED,
    BurnsSemanticStatus.PROBABLE_CULTIC,
}


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _headword_tokens(value: str, *, strip_markers: bool) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw in value.split():
        token = _nfc(raw)
        if strip_markers:
            token = token.rstrip(EDITORIAL_MARKERS)
        if token:
            tokens.append(token)
    return tuple(tokens)


def _spans(words: tuple[int, ...], word_values: dict[int, str] | object, tokens: tuple[str, ...]) -> tuple[tuple[int, ...], ...]:
    if not tokens:
        return ()
    values = tuple(_nfc(word_values[word]) for word in words)  # type: ignore[index]
    width = len(tokens)
    matches: list[tuple[int, ...]] = []
    for start in range(0, len(values) - width + 1):
        if values[start : start + width] == tokens:
            matches.append(words[start : start + width])
    return tuple(matches)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuc", required=True)
    args = parser.parse_args()

    workbooks = ensure(WORKBOOKS, root=ROOT)
    source = load_pdf_directory(workbooks)
    normalized = normalize_workbook_records(source.records)
    index = build_reviewed_cuc_index(args.cuc)

    counts = Counter()
    lexical = {
        "exact": Counter(),
        "strip_editorial_markers": Counter(),
    }
    token_shapes = Counter()
    positive_spans: dict[int, list[tuple[str, tuple[int, ...]]]] = defaultdict(list)

    for annotation in normalized.annotations:
        counts["annotations"] += 1
        counts[f"semantic:{annotation.semantic_status.value}"] += 1
        if annotation.textual_status is BurnsTextualStatus.NON_TEXTUAL_NOT_ATTESTED:
            counts["non_textual"] += 1
            continue

        parsed = parse_burns_reference(
            ktu=annotation.ktu,
            reference=annotation.references,
            textual_status=annotation.textual_status,
        )
        counts[f"parse:{parsed.status.value}"] += 1
        if parsed.status is not BurnsReferenceStatus.PARSED:
            counts["unresolved_parse"] += 1
            continue

        tablet = parsed.targets[0].tablet
        tablet_node = index.tablet_nodes.get(tablet)
        if tablet_node is None:
            counts["out_of_cuc"] += 1
            continue

        if len(parsed.targets) == 1 and parsed.targets[0].line is None:
            counts["tablet_only"] += 1
            continue

        resolved_lines: list[int] = []
        line_resolution_failed = False
        for target in parsed.targets:
            assert target.line is not None
            if target.column is not None:
                node = index.line_nodes.get((target.tablet, target.column, target.line))
                if node is None:
                    counts["line:no_match"] += 1
                    line_resolution_failed = True
                    continue
                counts["line:unique_explicit_column"] += 1
                resolved_lines.append(node)
            else:
                candidates = index.bare_line_candidates.get((target.tablet, target.line), ())
                if not candidates:
                    counts["line:no_match"] += 1
                    line_resolution_failed = True
                elif len(candidates) == 1:
                    counts["line:unique_bare"] += 1
                    resolved_lines.append(candidates[0])
                else:
                    counts["line:ambiguous_bare"] += 1
                    counts[f"line:ambiguous_candidate_count:{len(candidates)}"] += 1
                    line_resolution_failed = True

        if line_resolution_failed:
            counts["annotations_with_unresolved_or_ambiguous_line"] += 1
        if not resolved_lines:
            continue

        raw_tokens = _headword_tokens(annotation.headword, strip_markers=False)
        stripped_tokens = _headword_tokens(annotation.headword, strip_markers=True)
        token_shapes[f"tokens:{len(raw_tokens)}"] += 1
        if raw_tokens != stripped_tokens:
            token_shapes["contains_trailing_editorial_marker"] += 1
        if not stripped_tokens:
            token_shapes["empty_after_marker_strip"] += 1

        for name, tokens in (
            ("exact", raw_tokens),
            ("strip_editorial_markers", stripped_tokens),
        ):
            per_annotation_matches = 0
            matched_lines = 0
            for line_node in resolved_lines:
                spans = _spans(index.line_words[line_node], index.word_g_cons, tokens)
                lexical[name][f"line_match_count:{len(spans)}"] += 1
                if spans:
                    matched_lines += 1
                    per_annotation_matches += len(spans)
                if (
                    name == "strip_editorial_markers"
                    and len(spans) == 1
                    and annotation.semantic_status in POSITIVE_STATUSES
                ):
                    positive_spans[line_node].append((annotation.annotation_id, spans[0]))
            lexical[name][f"annotation_total_span_matches:{per_annotation_matches}"] += 1
            lexical[name][f"annotation_matched_line_count:{matched_lines}"] += 1

    overlap_pairs = 0
    multiply_annotated_words: Counter[int] = Counter()
    for entries in positive_spans.values():
        for annotation_id, span in entries:
            for word in span:
                multiply_annotated_words[word] += 1
        for i, (left_id, left_span) in enumerate(entries):
            left = set(left_span)
            for right_id, right_span in entries[i + 1 :]:
                if left_id != right_id and left.intersection(right_span):
                    overlap_pairs += 1

    output = {
        "source": {
            "tree_sha256": source.tree_sha256,
            "files": len(source.files),
            "records": len(normalized.records),
            "annotations": len(normalized.annotations),
        },
        "counts": dict(sorted(counts.items())),
        "headword_token_shapes": dict(sorted(token_shapes.items())),
        "lexical_matching": {
            name: dict(sorted(strategy.items()))
            for name, strategy in lexical.items()
        },
        "positive_overlap_lower_bounds": {
            "overlapping_pairs_same_resolved_line": overlap_pairs,
            "words_with_multiple_positive_annotations": sum(
                1 for count in multiply_annotated_words.values() if count > 1
            ),
            "max_positive_annotations_on_one_word": max(
                multiply_annotated_words.values(), default=0
            ),
        },
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
