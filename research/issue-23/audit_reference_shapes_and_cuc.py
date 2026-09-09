#!/usr/bin/env python3
"""Source-safe research probe for issue #23.

Downloads the checksum-pinned Burns Workbooks through the existing helper and
loads a caller-supplied CUC TF 0.2.8 directory. Output is aggregate-only:
reference wording is replaced by structural symbols and no Burns-derived row or
artifact is persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from tf.fabric import Fabric

from scripts.sources import WORKBOOKS, ensure
from ugarit_context_parsing.annotations import (
    BurnsTextualStatus,
    normalize_workbook_records,
)
from ugarit_context_parsing.pdf_source import load_pdf_directory

CUC_COMMIT = "ad69400f5446e1c8217af01659c7c10ab00c015b"
CUC_VERSION = "0.2.8"
REQUIRED_FILES = (
    "otype.tf",
    "oslots.tf",
    "tablet.tf",
    "column.tf",
    "line.tf",
    "g_cons.tf",
)
_ROMAN_TOKEN = re.compile(r"(?<![\w])(?:[IVXLCDM]+)(?![\w])")
_NUMBER = re.compile(r"\d+")
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_SPACE = re.compile(r"\s+")


def structural_shape(text: str) -> str:
    value = unicodedata.normalize("NFC", text.strip())
    value = _ROMAN_TOKEN.sub("R", value)
    value = _NUMBER.sub("N", value)
    value = _WORD.sub("W", value)
    return _SPACE.sub(" ", value).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cuc_probe(cuc_tf: Path) -> dict[str, object]:
    file_fingerprint: dict[str, dict[str, object]] = {}
    for name in REQUIRED_FILES:
        path = cuc_tf / name
        if not path.is_file():
            raise RuntimeError(f"missing required reviewed CUC feature: {name}")
        file_fingerprint[name] = {
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }

    manifest_payload = json.dumps(
        file_fingerprint,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    aggregate_sha256 = hashlib.sha256(manifest_payload).hexdigest()

    api = Fabric(locations=[str(cuc_tf)], modules=[""], silent="deep").load(
        "tablet column line g_cons",
        silent="deep",
    )
    if api is None:
        raise RuntimeError(f"could not load CUC Text-Fabric from {cuc_tf}")

    counts = {
        otype: len(tuple(api.F.otype.s(otype)))
        for otype in ("sign", "word", "line", "column", "tablet")
    }

    tablet_keys: dict[str, list[int]] = defaultdict(list)
    for node in api.F.otype.s("tablet"):
        label = api.F.tablet.v(node)
        if label is not None:
            tablet_keys[str(label)].append(int(node))

    line_keys: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    lines_by_tablet_number: dict[tuple[str, int], list[int]] = defaultdict(list)
    words_per_line: Counter[int] = Counter()
    empty_g_cons_words = 0
    for line_node in api.F.otype.s("line"):
        section = api.T.sectionFromNode(line_node)
        if not section or len(section) != 3:
            continue
        tablet, column, line = section
        exact = (str(tablet), str(column), int(line))
        line_keys[exact].append(int(line_node))
        lines_by_tablet_number[(str(tablet), int(line))].append(int(line_node))
        words = tuple(api.L.d(line_node, otype="word"))
        words_per_line[len(words)] += 1
        for word in words:
            if api.F.g_cons.v(word) in (None, ""):
                empty_g_cons_words += 1

    return {
        "reviewed_commit": CUC_COMMIT,
        "tf_version": CUC_VERSION,
        "required_file_fingerprint": file_fingerprint,
        "required_files_manifest_sha256": aggregate_sha256,
        "otype_counts": counts,
        "duplicate_tablet_labels": sum(1 for nodes in tablet_keys.values() if len(nodes) != 1),
        "duplicate_exact_line_keys": sum(1 for nodes in line_keys.values() if len(nodes) != 1),
        "tablet_line_numbers_with_multiple_columns": sum(
            1 for nodes in lines_by_tablet_number.values() if len(nodes) > 1
        ),
        "max_columns_for_same_tablet_line_number": max(
            (len(nodes) for nodes in lines_by_tablet_number.values()),
            default=0,
        ),
        "empty_g_cons_word_nodes": empty_g_cons_words,
        "words_per_line": {str(k): v for k, v in sorted(words_per_line.items())},
    }


def burns_probe() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="burns-issue23-shapes-") as tmp:
        root = ensure(WORKBOOKS, root=Path(tmp))
        source = load_pdf_directory(root)
        normalized = normalize_workbook_records(source.records)

        shapes: Counter[str] = Counter()
        textual_shapes: Counter[str] = Counter()
        empty_textual = 0
        non_textual = 0
        for annotation in normalized.annotations:
            if annotation.textual_status is BurnsTextualStatus.NON_TEXTUAL_NOT_ATTESTED:
                non_textual += 1
                continue
            shape = structural_shape(annotation.references)
            if not shape:
                empty_textual += 1
                continue
            shapes[shape] += 1
            textual_shapes[shape] += 1

        return {
            "pdfs": len(source.files),
            "records": len(normalized.records),
            "annotations": len(normalized.annotations),
            "non_textual_annotations": non_textual,
            "empty_textual_reference_annotations": empty_textual,
            "distinct_structural_shapes": len(shapes),
            "top_structural_shapes": [
                {"shape": shape, "count": count}
                for shape, count in textual_shapes.most_common(80)
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuc-tf", type=Path, required=True)
    args = parser.parse_args()

    result = {
        "privacy": "aggregate structural symbols only; no Burns wording or rows persisted",
        "burns": burns_probe(),
        "cuc": cuc_probe(args.cuc_tf.resolve()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
