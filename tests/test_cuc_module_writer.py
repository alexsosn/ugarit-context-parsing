from __future__ import annotations

import json
import unittest

from ugarit_context_parsing.alignment import (
    BurnsAlignmentConfidence,
    BurnsAlignmentDisposition,
    BurnsAlignmentOccurrence,
    BurnsAlignmentReason,
    BurnsAnchorKind,
)
from ugarit_context_parsing.annotations import (
    BurnsAnnotation,
    BurnsInterpretiveStatus,
    BurnsSemanticStatus,
    BurnsTextualStatus,
    BurnsWorksheetRole,
)
from ugarit_context_parsing.references import BurnsTarget
from ugarit_context_parsing.module_writer import build_module_features


def annotation(annotation_id: str, headword: str) -> BurnsAnnotation:
    return BurnsAnnotation(
        annotation_id=annotation_id,
        worksheet_id="01 Synthetic/Synthetic Worksheet 1",
        workbook_number=1,
        workbook_label="01 Synthetic",
        worksheet_number=1,
        worksheet_role=BurnsWorksheetRole.PRIME_GP,
        first_source_row=1,
        section="Section synthetic",
        root="",
        headword=headword,
        ktu="1.1",
        references="1",
        textual_status=BurnsTextualStatus.TEXTUAL,
        semantic_status=BurnsSemanticStatus.POSITIVE_FIXED,
        interpretive_status=BurnsInterpretiveStatus.UNSPECIFIED,
        record_ids=(f"record-{annotation_id}",),
    )


def occurrence(occurrence_id: str, nodes: tuple[int, ...]) -> BurnsAlignmentOccurrence:
    return BurnsAlignmentOccurrence(
        occurrence_id=occurrence_id,
        target_ordinal=0,
        target=BurnsTarget(tablet="KTU 1.1", column="I", line=1),
        disposition=BurnsAlignmentDisposition.ALIGNED,
        reason=BurnsAlignmentReason.NONE,
        confidence=BurnsAlignmentConfidence.EXACT_LEXICAL,
        anchor_kind=BurnsAnchorKind.WORD_SPAN,
        anchor_nodes=nodes,
        context_line_node=50,
    )


class BurnsModuleFeatureTests(unittest.TestCase):
    def test_multiplicity_span_identity_and_order_are_lossless(self):
        a = annotation("ann-a", "alpha\nmarked")
        b = annotation("ann-b", "beta ! punctuation")
        occ_a = occurrence("occ-a", (101, 102))
        occ_b = occurrence("occ-b", (102,))

        first = build_module_features([(b, occ_b), (a, occ_a), (a, occ_a)])
        second = build_module_features([(a, occ_a), (b, occ_b)])
        self.assertEqual(first, second)
        self.assertNotIn("otype", first)
        self.assertNotIn("oslots", first)

        payload_101 = json.loads(first["burns_annotations"][101])
        payload_102 = json.loads(first["burns_annotations"][102])
        self.assertEqual(len(payload_101), 1)
        self.assertEqual(len(payload_102), 2)
        self.assertEqual(payload_101[0]["anchor_nodes"], [101, 102])
        self.assertEqual(payload_101[0]["occurrence_id"], "occ-a")
        self.assertEqual(payload_101[0]["headword"], "alpha\nmarked")
        self.assertEqual(
            {(entry["occurrence_id"], tuple(entry["anchor_nodes"])) for entry in payload_102},
            {("occ-a", (101, 102)), ("occ-b", (102,))},
        )

    def test_unanchored_occurrence_is_not_guessed_onto_a_node(self):
        a = annotation("ann-a", "alpha")
        unresolved = BurnsAlignmentOccurrence(
            occurrence_id="occ-none",
            target_ordinal=0,
            target=BurnsTarget(tablet="KTU 1.1", column="I", line=999),
            disposition=BurnsAlignmentDisposition.UNRESOLVED_REFERENCE,
            reason=BurnsAlignmentReason.LINE_NOT_FOUND,
            confidence=BurnsAlignmentConfidence.NONE,
            anchor_kind=None,
            anchor_nodes=(),
            context_line_node=None,
        )
        self.assertEqual(build_module_features([(a, unresolved)]), {})


if __name__ == "__main__":
    unittest.main()
