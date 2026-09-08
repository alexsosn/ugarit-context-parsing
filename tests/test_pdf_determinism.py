from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pdfplumber
from tf.fabric import Fabric

from scripts.parse_workbooks_to_csv import CANONICAL_BOUNDS, file_bounds
from ugarit_context_parsing._semantic_compare import compare_text_fabric_artifacts
from ugarit_context_parsing.cli import main


_CANONICAL_BOUNDS = (69, 166, 197, 296, 373, 438, 504, 553, 574, 772)


def _source_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_synthetic_pdf(
    path: Path,
    text_items: tuple[tuple[int, int, str], ...],
    *,
    vertical_lines: tuple[int, ...] = (),
) -> None:
    """Write a deterministic one-page PDF using only standard PDF syntax."""
    commands = [
        f"BT /F1 10 Tf 1 0 0 1 {x} {y} Tm ({_pdf_escape(text)}) Tj ET"
        for x, y, text in text_items
    ]
    commands.extend(f"{x} 80 m {x} 450 l S" for x in vertical_lines)
    content = ("\n".join(commands) + "\n").encode("latin-1")

    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        5: b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
    }

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: dict[int, int] = {}
    for number in range(1, 6):
        offsets[number] = len(pdf)
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(objects[number])
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 6\n")
    pdf.extend(b"0000000000 65535 f \n")
    for number in range(1, 6):
        pdf.extend(f"{offsets[number]:010d} 00000 n \n".encode("ascii"))
    pdf.extend(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n")
    pdf.extend(str(xref_offset).encode("ascii"))
    pdf.extend(b"\n%%EOF\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)


def _write_pdf_determinism_fixture(source: Path, *, later_first: bool) -> None:
    ruled = (
        (80, 410, "Section Synthetic"),
        (80, 390, "\\zr"),
        (175, 390, "1.14"),
        (210, 390, "I 1"),
        (310, 390, "GP"),
        (380, 390, "1"),
        (80, 370, "wrapped"),
        (175, 350, "1.15"),
        (210, 350, "II 2"),
        (310, 350, "PH"),
        (380, 350, "2"),
        (310, 330, "PH"),
        (380, 330, "3"),
        (210, 310, "continued"),
        (600, 310, "comment"),
    )
    fallback = (
        (80, 410, "Section Fallback"),
        (80, 390, "mlk"),
        (175, 390, "1.16"),
        (210, 390, "III 3"),
        (310, 390, "GP"),
        (380, 390, "4"),
    )
    files = [
        (source / "Alpha" / "Ruled.pdf", ruled, _CANONICAL_BOUNDS),
        (source / "Zeta" / "Fallback.pdf", fallback, ()),
    ]
    if later_first:
        files.reverse()
    for path, text_items, vertical_lines in files:
        _write_synthetic_pdf(path, text_items, vertical_lines=vertical_lines)


def _assert_pdf_geometry_contract(testcase: unittest.TestCase, source: Path) -> None:
    ruled_path = source / "Alpha" / "Ruled.pdf"
    with pdfplumber.open(str(ruled_path)) as pdf:
        vertical_edges = [
            edge
            for page in pdf.pages
            for edge in page.edges
            if edge["orientation"] == "v"
        ]
        testcase.assertEqual(len(vertical_edges), 10)
        testcase.assertEqual(file_bounds(pdf), tuple(float(x) for x in _CANONICAL_BOUNDS))

    fallback_path = source / "Zeta" / "Fallback.pdf"
    with pdfplumber.open(str(fallback_path)) as pdf:
        vertical_edges = [
            edge
            for page in pdf.pages
            for edge in page.edges
            if edge["orientation"] == "v"
        ]
        testcase.assertEqual(vertical_edges, [])
        testcase.assertEqual(file_bounds(pdf), CANONICAL_BOUNDS)


def _assert_synthetic_pdf_contract(testcase: unittest.TestCase, output: Path) -> None:
    report = json.loads((output / "conversion-report.json").read_text(encoding="utf-8"))
    testcase.assertEqual(report["status"], "ok")
    testcase.assertEqual(report["source"]["format"], "pdf")
    testcase.assertEqual(report["source"]["file_count"], 2)
    testcase.assertEqual(report["counts"]["records"], 4)

    api = Fabric(locations=[str(output)], modules=[""], silent="deep").load(
        "headword ktu cuc_tablet references comments source_file source_page",
        silent="deep",
    )
    testcase.assertIsNotNone(api)
    assert api is not None

    records = tuple(api.F.otype.s("record"))
    testcase.assertEqual(records, (1, 2, 3, 4))
    testcase.assertEqual(
        [api.F.source_file.v(node) for node in records],
        ["Alpha/Ruled.pdf", "Alpha/Ruled.pdf", "Alpha/Ruled.pdf", "Zeta/Fallback.pdf"],
    )
    testcase.assertEqual([api.F.source_page.v(node) for node in records], [1, 1, 1, 1])
    testcase.assertEqual(
        [api.F.headword.v(node) for node in records],
        ["ġzr wrapped", "ġzr wrapped", "ġzr wrapped", "mlk"],
    )
    testcase.assertEqual(
        [api.F.ktu.v(node) for node in records],
        ["1.14", "1.15", "1.15", "1.16"],
    )
    testcase.assertEqual(
        [api.F.cuc_tablet.v(node) for node in records],
        ["KTU 1.14", "KTU 1.15", "KTU 1.15", "KTU 1.16"],
    )
    testcase.assertEqual(
        [api.F.references.v(node) for node in records],
        ["I 1", "II 2 continued", "II 2 continued", "III 3"],
    )
    testcase.assertEqual(
        [api.F.comments.v(node) for node in records],
        [None, None, "comment", None],
    )

    worksheets = tuple(api.F.otype.s("worksheet"))
    testcase.assertEqual(len(worksheets), 2)
    testcase.assertEqual(
        [api.T.sectionFromNode(node)[0] for node in worksheets],
        ["Alpha/Ruled", "Zeta/Fallback"],
    )


class RealPdfDeterminismTests(unittest.TestCase):
    def test_repeated_synthetic_pdf_materialization_is_semantically_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_a = root / "pdf-a"
            source_b = root / "pdf-b"
            _write_pdf_determinism_fixture(source_a, later_first=True)
            _write_pdf_determinism_fixture(source_b, later_first=False)

            source_before_a = _source_snapshot(source_a)
            source_before_b = _source_snapshot(source_b)
            self.assertEqual(source_before_a, source_before_b)
            self.assertEqual(
                tuple(source_before_a),
                ("Alpha/Ruled.pdf", "Zeta/Fallback.pdf"),
            )
            _assert_pdf_geometry_contract(self, source_a)
            _assert_pdf_geometry_contract(self, source_b)

            output_a = root / "tf-a"
            output_b = root / "tf-b"
            for source, output in ((source_a, output_a), (source_b, output_b)):
                self.assertEqual(
                    main([
                        "convert",
                        str(source),
                        "--input-format",
                        "pdf",
                        "--output",
                        str(output),
                    ]),
                    0,
                )

            self.assertEqual(_source_snapshot(source_a), source_before_a)
            self.assertEqual(_source_snapshot(source_b), source_before_b)
            self.assertEqual(_source_snapshot(source_a), _source_snapshot(source_b))
            self.assertEqual(compare_text_fabric_artifacts(output_a, output_b), ())

            _assert_synthetic_pdf_contract(self, output_a)
            _assert_synthetic_pdf_contract(self, output_b)


if __name__ == "__main__":
    unittest.main()
