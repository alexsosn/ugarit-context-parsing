from __future__ import annotations

import unittest

from ugarit_context_parsing.annotations import BurnsTextualStatus
from ugarit_context_parsing.references import (
    BurnsReferenceReason,
    BurnsReferenceStatus,
    BurnsTarget,
    parse_burns_reference,
)


class BurnsRomanColumnValidityTests(unittest.TestCase):
    def test_canonical_roman_column_is_supported(self):
        result = parse_burns_reference(
            ktu="1.14",
            reference="VIII.3",
            textual_status=BurnsTextualStatus.TEXTUAL,
        )
        self.assertEqual(result.status, BurnsReferenceStatus.PARSED)
        self.assertEqual(result.targets, (BurnsTarget("KTU 1.14", "VIII", 3),))

    def test_noncanonical_roman_columns_fail_closed(self):
        for reference in ("VX.3", "IIV.3", "IIII.3", "IC.3"):
            with self.subTest(reference=reference):
                result = parse_burns_reference(
                    ktu="1.14",
                    reference=reference,
                    textual_status=BurnsTextualStatus.TEXTUAL,
                )
                self.assertEqual(result.status, BurnsReferenceStatus.MALFORMED)
                self.assertEqual(result.reason, BurnsReferenceReason.MALFORMED_STRUCTURE)
                self.assertEqual(result.targets, ())


if __name__ == "__main__":
    unittest.main()
