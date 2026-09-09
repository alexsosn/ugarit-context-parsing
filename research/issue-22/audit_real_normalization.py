#!/usr/bin/env python3
"""Aggregate-only real-source validation of the #22 production normalizer."""
from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

from scripts.sources import WORKBOOKS, ensure
from ugarit_context_parsing.annotations import normalize_workbook_records
from ugarit_context_parsing.pdf_source import load_pdf_directory

EXPECTED = {
    "rows": 13857,
    "annotations": 10419,
    "semantic": {
        "positive_fixed": 2675,
        "probable_cultic": 1018,
        "no_secure_cultic": 2091,
        "homograph_excluded": 4635,
    },
    "worksheets": {
        "prime_gp": 2595,
        "prime_ph": 1284,
        "derived_common": 3326,
        "derived_gp_only": 1458,
        "derived_ph_only": 1756,
    },
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="burns-issue22-production-audit-") as tmp:
        input_root = ensure(WORKBOOKS, root=Path(tmp))
        source = load_pdf_directory(input_root)
        normalized = normalize_workbook_records(source.records)

        semantic = Counter(record.semantic_status.value for record in normalized.records)
        # Semantic status is row-level as well as annotation-level, but the audit
        # target is authored annotations. Count from annotations explicitly.
        semantic_annotations = Counter(
            annotation.semantic_status.value for annotation in normalized.annotations
        )
        worksheet_annotations = Counter(
            annotation.worksheet_role.value for annotation in normalized.annotations
        )

        result = {
            "pdfs": len(source.files),
            "rows": len(normalized.records),
            "annotations": len(normalized.annotations),
            "semantic_annotations": dict(sorted(semantic_annotations.items())),
            "worksheet_annotations": dict(sorted(worksheet_annotations.items())),
        }
        print(result)

        assert len(source.files) == 45, result
        assert len(normalized.records) == EXPECTED["rows"], result
        assert len(normalized.annotations) == EXPECTED["annotations"], result
        assert dict(semantic_annotations) == EXPECTED["semantic"], result
        assert dict(worksheet_annotations) == EXPECTED["worksheets"], result
        # Make accidental future confusion explicit: row-level semantic counts
        # need not equal authored-annotation semantic counts.
        assert sum(semantic.values()) == EXPECTED["rows"]

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
