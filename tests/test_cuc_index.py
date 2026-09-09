from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from ugarit_context_parsing.cuc_index import (
    REVIEWED_CUC_COMMIT,
    REVIEWED_CUC_COUNTS,
    REVIEWED_CUC_FILES,
    REVIEWED_CUC_MANIFEST_SHA256,
    REVIEWED_CUC_REPOSITORY,
    REVIEWED_CUC_VERSION,
    CucColumnRow,
    CucCompatibilityError,
    CucLineRow,
    CucStructuralSnapshot,
    CucTabletRow,
    _build_index_from_snapshot,
    _verify_reviewed_cuc_files,
    build_reviewed_cuc_index,
)


SYNTHETIC_COUNTS = {
    "sign": 8,
    "column": 3,
    "line": 4,
    "tablet": 2,
    "word": 6,
}


def snapshot(
    *,
    tablets: tuple[CucTabletRow, ...] | None = None,
    columns: tuple[CucColumnRow, ...] | None = None,
    lines: tuple[CucLineRow, ...] | None = None,
    word_g_cons: tuple[tuple[int, str], ...] | None = None,
    counts: dict[str, int] | None = None,
    section_types: tuple[str, ...] = ("tablet", "column", "line"),
    section_features: tuple[str, ...] = ("tablet", "column", "line"),
) -> CucStructuralSnapshot:
    return CucStructuralSnapshot(
        counts=tuple(sorted((counts or SYNTHETIC_COUNTS).items())),
        section_types=section_types,
        section_features=section_features,
        tablets=tablets
        or (
            CucTabletRow(100, "KTU 1.1"),
            CucTabletRow(101, "KTU 1.2"),
        ),
        columns=columns
        or (
            CucColumnRow(110, "KTU 1.1", "I"),
            CucColumnRow(111, "KTU 1.1", "II"),
            CucColumnRow(112, "KTU 1.2", "I"),
        ),
        lines=lines
        or (
            CucLineRow(200, "KTU 1.1", "I", 1, (300, 301)),
            CucLineRow(201, "KTU 1.1", "I", 2, (302,)),
            CucLineRow(202, "KTU 1.1", "II", 2, (303, 304)),
            CucLineRow(203, "KTU 1.2", "I", 1, (305,)),
        ),
        word_g_cons=word_g_cons
        or (
            (300, "bʿl"),
            (301, "mlk"),
            (302, ""),
            (303, "ym"),
            (304, "špš"),
            (305, "qrb"),
        ),
    )


class CucReviewedConstantsTests(unittest.TestCase):
    def test_reviewed_identity_constants_are_exact(self):
        self.assertEqual(REVIEWED_CUC_REPOSITORY, "DT-UCPH/cuc")
        self.assertEqual(
            REVIEWED_CUC_COMMIT,
            "ad69400f5446e1c8217af01659c7c10ab00c015b",
        )
        self.assertEqual(REVIEWED_CUC_VERSION, "0.2.8")
        self.assertEqual(
            REVIEWED_CUC_COUNTS,
            {
                "sign": 146017,
                "column": 334,
                "line": 7616,
                "tablet": 279,
                "word": 27770,
            },
        )

    def test_required_file_manifest_is_the_researched_six_file_contract(self):
        expected = {
            "otype.tf": (531, "d3ab2f599b7a1e1029608670c739b8439986a7be092d5d1b5eac5267a2ad554f"),
            "oslots.tf": (448752, "362c5bdd944cc6c2658634b83747f5796e61922bf81164e05ac8ebd579da85c8"),
            "tablet.tf": (3036, "db3429847e6daf67dd07452a72615ac999aa4419ea101b1e0312d294ceff05ef"),
            "column.tf": (1200, "0485fc45900d039a0227ad6c418530d1dfa373393bb3b5e9f0614066c26aaa17"),
            "line.tf": (20566, "a2e8122ffe274ff47b4b1f64f9a54dd623ec57d48bf95f74152bad35fff3fcf8"),
            "g_cons.tf": (124223, "7ac1a6a4c2641aa1b2579e8c204fcb93f18f9d6629c950054482cd2983dbcd80"),
        }
        self.assertEqual(set(REVIEWED_CUC_FILES), set(expected))
        for name, (size, sha256) in expected.items():
            with self.subTest(name=name):
                fingerprint = REVIEWED_CUC_FILES[name]
                self.assertEqual(fingerprint.size, size)
                self.assertEqual(fingerprint.sha256, sha256)

        payload = {
            name: {"sha256": item.sha256, "size": item.size}
            for name, item in REVIEWED_CUC_FILES.items()
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(encoded).hexdigest(),
            REVIEWED_CUC_MANIFEST_SHA256,
        )
        self.assertEqual(
            REVIEWED_CUC_MANIFEST_SHA256,
            "717e5b7f1c60b800e05f50f4cac27dac7562b45eecb48a8686c64cfab42a92ba",
        )


class CucPureIndexBuilderTests(unittest.TestCase):
    def build(self, data: CucStructuralSnapshot | None = None):
        return _build_index_from_snapshot(
            data or snapshot(),
            expected_counts=SYNTHETIC_COUNTS,
            expected_section_types=("tablet", "column", "line"),
            expected_section_features=("tablet", "column", "line"),
        )

    def test_builds_all_structural_indexes_without_selecting_ambiguous_line(self):
        index = self.build()

        self.assertEqual(index.tablet_nodes["KTU 1.1"], 100)
        self.assertEqual(index.column_nodes[("KTU 1.1", "II")], 111)
        self.assertEqual(index.line_nodes[("KTU 1.1", "II", 2)], 202)
        self.assertEqual(index.bare_line_candidates[("KTU 1.1", 2)], (201, 202))
        self.assertEqual(index.line_words[200], (300, 301))
        self.assertEqual(index.word_g_cons[300], "bʿl")
        self.assertEqual(index.word_g_cons[302], "")

    def test_candidate_order_is_deterministic_even_if_snapshot_lines_are_reordered(self):
        data = snapshot()
        reversed_data = snapshot(lines=tuple(reversed(data.lines)))
        a = self.build(data)
        b = self.build(reversed_data)
        self.assertEqual(a.bare_line_candidates, b.bare_line_candidates)
        self.assertEqual(a.line_nodes, b.line_nodes)
        self.assertEqual(b.bare_line_candidates[("KTU 1.1", 2)], (201, 202))

    def test_index_mappings_are_read_only(self):
        index = self.build()
        for mapping in (
            index.tablet_nodes,
            index.column_nodes,
            index.line_nodes,
            index.bare_line_candidates,
            index.line_words,
            index.word_g_cons,
        ):
            self.assertIsInstance(mapping, MappingProxyType)
        with self.assertRaises(TypeError):
            index.tablet_nodes["KTU 9.9"] = 999  # type: ignore[index]

    def test_duplicate_tablet_label_fails_closed(self):
        data = snapshot(
            tablets=(
                CucTabletRow(100, "KTU 1.1"),
                CucTabletRow(101, "KTU 1.1"),
            )
        )
        with self.assertRaisesRegex(CucCompatibilityError, "duplicate tablet"):
            self.build(data)

    def test_duplicate_column_key_fails_closed(self):
        data = snapshot(
            columns=(
                CucColumnRow(110, "KTU 1.1", "I"),
                CucColumnRow(111, "KTU 1.1", "I"),
                CucColumnRow(112, "KTU 1.2", "I"),
            )
        )
        with self.assertRaisesRegex(CucCompatibilityError, "duplicate column"):
            self.build(data)

    def test_duplicate_exact_line_key_fails_closed(self):
        data = snapshot(
            lines=(
                CucLineRow(200, "KTU 1.1", "I", 1, (300,)),
                CucLineRow(201, "KTU 1.1", "I", 2, (301,)),
                CucLineRow(202, "KTU 1.1", "I", 2, (302,)),
                CucLineRow(203, "KTU 1.2", "I", 1, (303,)),
            )
        )
        with self.assertRaisesRegex(CucCompatibilityError, "duplicate.*line"):
            self.build(data)

    def test_type_count_mismatch_fails_closed(self):
        data = snapshot(counts={**SYNTHETIC_COUNTS, "tablet": 3})
        with self.assertRaisesRegex(CucCompatibilityError, "count"):
            self.build(data)

    def test_section_type_mismatch_fails_closed(self):
        data = snapshot(section_types=("tablet", "line"))
        with self.assertRaisesRegex(CucCompatibilityError, "section"):
            self.build(data)

    def test_section_feature_mismatch_fails_closed(self):
        data = snapshot(section_features=("tablet", "line"))
        with self.assertRaisesRegex(CucCompatibilityError, "section"):
            self.build(data)

    def test_missing_word_g_cons_is_not_silently_coerced(self):
        data = snapshot(word_g_cons=tuple((node, value) for node, value in snapshot().word_g_cons if node != 304))
        with self.assertRaisesRegex(CucCompatibilityError, "g_cons"):
            self.build(data)


class CucPublicFingerprintGateTests(unittest.TestCase):
    def test_missing_required_file_fails_before_tf_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(CucCompatibilityError, "missing|required"):
                build_reviewed_cuc_index(root)

    def test_required_file_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real.tf"
            target.write_text("synthetic", encoding="utf-8")
            link = root / "otype.tf"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaisesRegex(CucCompatibilityError, "symlink"):
                build_reviewed_cuc_index(root)

    def test_one_byte_fingerprint_perturbation_fails_without_loading_tf(self):
        # Build all six required paths as ordinary files. Their bytes are
        # intentionally synthetic, so verification must stop at fingerprinting.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REVIEWED_CUC_FILES:
                (root / name).write_bytes(b"synthetic")
            with self.assertRaisesRegex(CucCompatibilityError, "fingerprint|sha|size"):
                build_reviewed_cuc_index(root)

    def test_private_file_verifier_returns_canonical_manifest_only_on_exact_bytes(self):
        # This negative control exercises the verifier directly without needing
        # to synthesize megabytes of reviewed CUC bytes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in REVIEWED_CUC_FILES:
                (root / name).write_bytes(b"x")
            with self.assertRaises(CucCompatibilityError):
                _verify_reviewed_cuc_files(root)

    def test_public_builder_rejects_non_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-a-dir"
            path.write_text("synthetic", encoding="utf-8")
            with self.assertRaisesRegex(CucCompatibilityError, "directory"):
                build_reviewed_cuc_index(path)

    def test_public_api_exposes_no_fingerprint_bypass_keywords(self):
        import inspect

        parameters = inspect.signature(build_reviewed_cuc_index).parameters
        for forbidden in {"skip_hash", "skip_fingerprint", "trust_version", "allow_mismatch"}:
            self.assertNotIn(forbidden, parameters)


if __name__ == "__main__":
    unittest.main()
