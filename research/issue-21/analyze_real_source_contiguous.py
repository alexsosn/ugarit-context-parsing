#!/usr/bin/env python3
"""Aggregate-only Burns/CUC audit using contiguous semantic source groups.

The source is the checksum-pinned Workbooks archive and the base is a caller-
supplied reviewed CUC TF checkout. The script prints aggregate counts only: it
never prints or persists Burns rows, headwords, references, comments, CSV, or TF
output.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from tf.fabric import Fabric

from scripts.parse_workbooks_to_csv import parse_pdf
from scripts.sources import WORKBOOKS, ensure
from ugarit_context_parsing.identifiers import normalize_cuc_tablet

CUC_VERSION = "0.2.8"
CUC_REVIEWED_COMMIT = "ad69400f5446e1c8217af01659c7c10ab00c015b"

_ROMAN = r"[IVXLCDM]+"
_REF_RE = re.compile(
    rf"(?:(?P<column>{_ROMAN})\s*[.:]?\s*)?"
    r"(?P<start>\d+)"
    r"(?:\s*[-–—]\s*(?P<end>\d+))?",
    re.IGNORECASE,
)
_WS_RE = re.compile(r"worksheet\s*([1-5])", re.IGNORECASE)
_MARKERS_RE = re.compile(r"[*†!?]+")
_WORDISH_RE = re.compile(r"[^0-9A-Za-zÀ-žʿʾšṯḥṣḫḏṭġśẓ]+", re.UNICODE)


@dataclass(frozen=True)
class SourceRow:
    source_file: str
    source_page: int
    section: str
    root: str
    headword: str
    ktu: str
    references: str
    locus: str
    room: str
    point: str
    depth: str
    disputed: str
    comments: str


@dataclass
class Annotation:
    source_file: str
    section: str
    root: str
    headword: str
    ktu: str
    references: str
    member_rows: int = 0
    comments: list[str] = field(default_factory=list)

    @property
    def category(self) -> str:
        parts = Path(self.source_file).parts
        return parts[0] if len(parts) > 1 else "(root)"

    @property
    def worksheet_role(self) -> str:
        match = _WS_RE.search(Path(self.source_file).stem)
        return match.group(1) if match else "unknown"

    @property
    def semantic_status(self) -> str:
        category = self.category
        if self.section == "Section β":
            return "homograph_excluded"
        if category[:2] in {"01", "02", "03", "04"} and self.section == "Section α":
            return "positive_fixed"
        if category[:2] in {"05", "06", "07", "08", "09"}:
            if self.section == "Section α1":
                return "probable_cultic"
            if self.section == "Section α2":
                return "no_secure_cultic"
        return "unsupported_or_unknown"

    @property
    def positive(self) -> bool:
        return self.semantic_status in {"positive_fixed", "probable_cultic"}


@dataclass(frozen=True)
class TargetRef:
    column: str | None
    line: int


@dataclass(frozen=True)
class ParsedRefs:
    targets: tuple[TargetRef, ...]
    quality: str


def parse_references(text: str) -> ParsedRefs:
    raw = unicodedata.normalize("NFC", text.strip())
    if not raw:
        return ParsedRefs((), "empty")

    targets: list[TargetRef] = []
    current_column: str | None = None
    consumed = [False] * len(raw)
    for match in _REF_RE.finditer(raw):
        column = match.group("column")
        if column:
            current_column = column.upper()
        start = int(match.group("start"))
        end_text = match.group("end")
        end = int(end_text) if end_text else start
        if end < start or end - start > 200:
            continue
        targets.extend(TargetRef(current_column, line) for line in range(start, end + 1))
        for offset in range(match.start(), match.end()):
            consumed[offset] = True

    residue = "".join(ch for offset, ch in enumerate(raw) if not consumed[offset])
    meaningful = re.sub(r"[\s,;:/().\[\]{}*†!?+&-]+", "", residue)
    quality = "simple" if targets and not meaningful else "complex"
    if not targets:
        quality = "unparsed"
    return ParsedRefs(tuple(dict.fromkeys(targets)), quality)


def _normalize_token(token: str) -> str:
    token = unicodedata.normalize("NFC", token)
    token = token.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
    token = _MARKERS_RE.sub("", token)
    return _WORDISH_RE.sub("", token).casefold()


def _headword_variants(text: str) -> tuple[tuple[str, ...], ...]:
    raw = unicodedata.normalize("NFC", text.strip())
    if not raw:
        return ()
    candidates = [raw, re.sub(r"\([^()]*\)", "", raw)]
    variants: list[tuple[str, ...]] = []
    for candidate in candidates:
        tokens = tuple(
            normalized
            for piece in candidate.split()
            if (normalized := _normalize_token(piece))
        )
        if tokens and tokens not in variants:
            variants.append(tokens)
    return tuple(variants)


def _group_key(row: SourceRow) -> tuple[str, str, str, str, str, str]:
    return (
        row.source_file,
        row.section,
        row.root,
        row.headword,
        row.ktu,
        row.references,
    )


def _collapse_contiguous(rows: list[SourceRow]) -> list[Annotation]:
    annotations: list[Annotation] = []
    current_key: tuple[str, str, str, str, str, str] | None = None
    current: Annotation | None = None

    for row in rows:
        key = _group_key(row)
        if key != current_key:
            current = Annotation(
                source_file=row.source_file,
                section=row.section,
                root=row.root,
                headword=row.headword,
                ktu=row.ktu,
                references=row.references,
            )
            annotations.append(current)
            current_key = key
        assert current is not None
        current.member_rows += 1
        if row.comments:
            current.comments.append(row.comments)
    return annotations


def _load_burns() -> tuple[list[SourceRow], list[Annotation], Counter[str]]:
    with tempfile.TemporaryDirectory(prefix="burns-issue21-contiguous-") as tmp:
        input_root = ensure(WORKBOOKS, root=Path(tmp))
        pdfs = sorted(input_root.glob("*/*.pdf"), key=lambda path: path.relative_to(input_root).as_posix())
        rows: list[SourceRow] = []
        pdf_counts: Counter[str] = Counter()
        for pdf in pdfs:
            rel = pdf.relative_to(input_root).as_posix()
            pdf_counts[Path(rel).parts[0]] += 1
            for item in parse_pdf(pdf):
                rows.append(
                    SourceRow(
                        source_file=rel,
                        source_page=int(item["source_page"]),
                        section=item["section"],
                        root=item["root"],
                        headword=item["headword"],
                        ktu=item["ktu"],
                        references=item["references"],
                        locus=item["locus"],
                        room=item["room"],
                        point=item["point"],
                        depth=item["depth"],
                        disputed=item["disputed"],
                        comments=item["comments"],
                    )
                )
        return rows, _collapse_contiguous(rows), pdf_counts


def _load_cuc(cuc_tf: Path):
    api = Fabric(locations=[str(cuc_tf)], modules=[""], silent="deep").load(
        "tablet column line g_cons",
        silent="deep",
    )
    if api is None:
        raise RuntimeError(f"could not load CUC Text-Fabric from {cuc_tf}")

    tablets: dict[str, int] = {}
    for node in api.F.otype.s("tablet"):
        label = api.F.tablet.v(node)
        if label:
            tablets[str(label)] = int(node)

    lines_exact: dict[tuple[str, str, int], int] = {}
    lines_by_number: dict[tuple[str, int], list[int]] = defaultdict(list)
    line_words: dict[int, tuple[tuple[int, str], ...]] = {}
    for line_node in api.F.otype.s("line"):
        section = api.T.sectionFromNode(line_node)
        if not section or len(section) != 3:
            continue
        tablet, column, line = section
        lines_exact[(str(tablet), str(column), int(line))] = int(line_node)
        lines_by_number[(str(tablet), int(line))].append(int(line_node))
        words: list[tuple[int, str]] = []
        for word in api.L.d(line_node, otype="word"):
            words.append((int(word), _normalize_token(str(api.F.g_cons.v(word) or ""))))
        line_words[int(line_node)] = tuple(words)

    return api, tablets, lines_exact, lines_by_number, line_words


def _resolve_lines(
    tablet: str,
    refs: ParsedRefs,
    lines_exact: dict[tuple[str, str, int], int],
    lines_by_number: dict[tuple[str, int], list[int]],
) -> tuple[tuple[int, ...], bool]:
    nodes: list[int] = []
    ambiguous = False
    for target in refs.targets:
        if target.column:
            node = lines_exact.get((tablet, target.column, target.line))
            if node is not None:
                nodes.append(node)
            continue
        candidates = lines_by_number.get((tablet, target.line), [])
        if len(candidates) == 1:
            nodes.append(candidates[0])
        elif len(candidates) > 1:
            ambiguous = True
    return tuple(dict.fromkeys(nodes)), ambiguous


def _find_spans(
    variants: tuple[tuple[str, ...], ...],
    line_nodes: tuple[int, ...],
    line_words: dict[int, tuple[tuple[int, str], ...]],
) -> tuple[tuple[int, ...], ...]:
    spans: list[tuple[int, ...]] = []
    for line_node in line_nodes:
        words = line_words.get(line_node, ())
        forms = tuple(form for _, form in words)
        for variant in variants:
            width = len(variant)
            if not width or width > len(forms):
                continue
            for start in range(len(forms) - width + 1):
                if forms[start : start + width] == variant:
                    spans.append(tuple(node for node, _ in words[start : start + width]))
    return tuple(dict.fromkeys(spans))


def _node_multiplicity(node_to_annotations: dict[int, set[int]]) -> dict[str, int]:
    return {
        "word_nodes_with_any_exact_annotation": len(node_to_annotations),
        "word_nodes_with_multiple_exact_annotations": sum(
            1 for ids in node_to_annotations.values() if len(ids) > 1
        ),
        "max_annotations_on_one_word": max(
            (len(ids) for ids in node_to_annotations.values()), default=0
        ),
    }


def _span_pair_counts(records: list[tuple[int, tuple[int, ...]]]) -> dict[str, int]:
    overlapping: set[tuple[int, int]] = set()
    nested: set[tuple[int, int]] = set()
    for left_pos, (left_id, left) in enumerate(records):
        left_set = set(left)
        for right_id, right in records[left_pos + 1 :]:
            right_set = set(right)
            if not left_set.intersection(right_set):
                continue
            pair = (min(left_id, right_id), max(left_id, right_id))
            overlapping.add(pair)
            if left_set <= right_set or right_set <= left_set:
                nested.add(pair)
    return {
        "overlapping_exact_annotation_pairs": len(overlapping),
        "nested_exact_annotation_pairs": len(nested),
    }


def analyze(cuc_tf: Path) -> dict[str, object]:
    rows, annotations, pdf_counts = _load_burns()
    api, tablets, lines_exact, lines_by_number, line_words = _load_cuc(cuc_tf)

    status_counts = Counter(annotation.semantic_status for annotation in annotations)
    worksheet_counts = Counter(annotation.worksheet_role for annotation in annotations)
    member_rows = Counter(annotation.member_rows for annotation in annotations)
    ref_quality: Counter[str] = Counter()
    ktu_status: Counter[str] = Counter()
    disposition: Counter[str] = Counter()
    comments: Counter[str] = Counter()

    all_nodes: dict[int, set[int]] = defaultdict(set)
    positive_nodes: dict[int, set[int]] = defaultdict(set)
    all_spans: list[tuple[int, tuple[int, ...]]] = []
    positive_spans: list[tuple[int, tuple[int, ...]]] = []

    for index, annotation in enumerate(annotations):
        refs = parse_references(annotation.references)
        ref_quality[refs.quality] += 1

        if annotation.comments:
            comments["nonempty"] += 1
            folded = " ".join(annotation.comments).casefold()
            if "?" in folded or any(
                term in folded for term in ("perhaps", "possibly", "probably", "uncertain")
            ):
                comments["uncertainty_signal"] += 1
            if any(
                term in folded for term in ("cf.", "see ", "compare", "alternative", "alternatively")
            ):
                comments["crossref_or_alternative_signal"] += 1

        if annotation.ktu.casefold().startswith("not attested"):
            ktu_status["not_attested"] += 1
            disposition["non_textual_not_attested"] += 1
            continue

        tablet = normalize_cuc_tablet(annotation.ktu)
        if not tablet:
            ktu_status["unparsed"] += 1
            disposition["ktu_unparsed"] += 1
            continue
        if tablet not in tablets:
            ktu_status["out_of_cuc"] += 1
            disposition["out_of_cuc"] += 1
            continue
        ktu_status["in_cuc"] += 1

        if not refs.targets:
            disposition["reference_unparsed"] += 1
            continue
        line_nodes, ambiguous_lines = _resolve_lines(
            tablet, refs, lines_exact, lines_by_number
        )
        if not line_nodes:
            disposition[
                "line_unresolved_ambiguous" if ambiguous_lines else "line_unresolved"
            ] += 1
            continue

        spans = _find_spans(_headword_variants(annotation.headword), line_nodes, line_words)
        if len(spans) == 1:
            disposition["exact_word_span_unique"] += 1
            span = spans[0]
            all_spans.append((index, span))
            for node in span:
                all_nodes[node].add(index)
            if annotation.positive:
                positive_spans.append((index, span))
                for node in span:
                    positive_nodes[node].add(index)
        elif len(spans) > 1:
            disposition["exact_word_span_multiple"] += 1
        else:
            disposition["line_resolved_headword_no_exact_match"] += 1

    all_mult = _node_multiplicity(all_nodes)
    all_mult.update(_span_pair_counts(all_spans))
    positive_mult = _node_multiplicity(positive_nodes)
    positive_mult.update(_span_pair_counts(positive_spans))

    return {
        "probe_contract": {
            "burns_source": "checksum-pinned Workbooks.zip via scripts/sources.py",
            "grouping": "contiguous authored runs by source_file/section/root/headword/ktu/references",
            "cuc_version": CUC_VERSION,
            "cuc_reviewed_commit": CUC_REVIEWED_COMMIT,
            "privacy": "aggregate counts only; no Burns-derived artifact persisted",
        },
        "source": {
            "pdfs": sum(pdf_counts.values()),
            "raw_rows": len(rows),
            "semantic_annotations": len(annotations),
            "raw_rows_collapsed": len(rows) - len(annotations),
            "semantic_status": dict(sorted(status_counts.items())),
            "worksheet_roles": dict(sorted(worksheet_counts.items())),
            "member_rows_per_annotation": {
                str(count): value for count, value in sorted(member_rows.items())
            },
        },
        "references": {"quality": dict(sorted(ref_quality.items()))},
        "comments": dict(sorted(comments.items())),
        "cuc_coverage": {
            "cuc_tablets": len(tablets),
            "ktu_status": dict(sorted(ktu_status.items())),
        },
        "alignment_lower_bound": dict(sorted(disposition.items())),
        "multiplicity_lower_bound": {
            "all_statuses": all_mult,
            "positive_alpha_alpha1_only": positive_mult,
        },
        "cuc_warp_counts": {
            "sign": len(tuple(api.F.otype.s("sign"))),
            "column": len(tuple(api.F.otype.s("column"))),
            "line": len(tuple(api.F.otype.s("line"))),
            "tablet": len(tuple(api.F.otype.s("tablet"))),
            "word": len(tuple(api.F.otype.s("word"))),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuc-tf", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.cuc_tf.resolve()), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
