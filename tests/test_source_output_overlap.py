from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stderr, redirect_stdout

from ugarit_context_parsing import cli


class SourceOutputOverlapTests(unittest.TestCase):
    @staticmethod
    def _source(root: Path):
        return SimpleNamespace(
            root=root.resolve(),
            files=("Workbook I/Worksheet 1.csv",),
            records=(object(),),
        )

    def _assert_convert_overlap_rejected(self, source_root: Path, output: Path) -> None:
        source = self._source(source_root)
        builder = Mock(return_value=object())
        reporter = Mock(return_value={"status": "ok"})
        writer = Mock(return_value=True)

        with (
            patch.object(cli, "load_csv_directory", return_value=source),
            patch.object(cli, "build_tf_data", builder),
            patch.object(cli, "build_conversion_report", reporter),
            patch.object(cli, "write_artifact", writer),
            redirect_stderr(io.StringIO()),
            self.assertRaisesRegex(SystemExit, "source/output paths must be disjoint"),
        ):
            cli.main(
                [
                    "convert",
                    str(source_root),
                    "--input-format",
                    "csv",
                    "--output",
                    str(output),
                ]
            )

        builder.assert_not_called()
        reporter.assert_not_called()
        writer.assert_not_called()

    def _assert_module_overlap_rejected(self, source_root: Path, output: Path) -> None:
        source = self._source(source_root)
        normalized = SimpleNamespace(records=(object(),), annotations=(object(),))
        normalizer = Mock(return_value=normalized)
        indexer = Mock(return_value=object())
        aligner = Mock(return_value=())
        builder = Mock(return_value=object())
        reporter = Mock(return_value={})
        writer = Mock(return_value=True)

        with (
            patch.object(cli, "load_csv_directory", return_value=source),
            patch.object(cli, "normalize_workbook_records", normalizer),
            patch.object(cli, "build_reviewed_cuc_index", indexer),
            patch.object(cli, "align_burns_source", aligner),
            patch.object(cli, "build_burns_module", builder),
            patch.object(cli, "build_burns_module_report", reporter),
            patch.object(cli, "write_burns_module", writer),
            redirect_stdout(io.StringIO()),
            self.assertRaisesRegex(SystemExit, "source/output paths must be disjoint"),
        ):
            cli.main(
                [
                    "module",
                    str(source_root),
                    "--input-format",
                    "csv",
                    "--cuc",
                    "cuc/tf/0.2.8",
                    "--output",
                    str(output),
                ]
            )

        normalizer.assert_not_called()
        indexer.assert_not_called()
        aligner.assert_not_called()
        builder.assert_not_called()
        reporter.assert_not_called()
        writer.assert_not_called()

    def test_convert_rejects_output_equal_to_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            source_root.mkdir()
            self._assert_convert_overlap_rejected(source_root, source_root)

    def test_module_rejects_output_equal_to_source_before_cuc_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            source_root.mkdir()
            self._assert_module_overlap_rejected(source_root, source_root)

    def test_output_nested_under_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            source_root.mkdir()
            self._assert_module_overlap_rejected(source_root, source_root / "generated" / "tf")

    def test_source_nested_under_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workspace"
            source_root = output / "input"
            source_root.mkdir(parents=True)
            self._assert_convert_overlap_rejected(source_root, output)

    def test_symlinked_ancestor_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_parent = root / "real-parent"
            source_root = real_parent / "source"
            source_root.mkdir(parents=True)
            linked_parent = root / "linked-parent"
            try:
                linked_parent.symlink_to(real_parent, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            aliased_output = linked_parent / "source" / "generated"
            self._assert_module_overlap_rejected(source_root, aliased_output)

    def test_disjoint_sibling_output_preserves_caller_path_and_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            output = root / "generated" / "legacy"
            source = self._source(source_root)
            data = object()
            report = {"status": "ok"}
            writer = Mock(return_value=True)

            with (
                patch.object(cli, "load_csv_directory", return_value=source),
                patch.object(cli, "build_tf_data", return_value=data),
                patch.object(cli, "build_conversion_report", return_value=report),
                patch.object(cli, "write_artifact", writer),
                redirect_stderr(io.StringIO()),
                redirect_stdout(io.StringIO()),
            ):
                result = cli.main(
                    [
                        "convert",
                        str(source_root),
                        "--input-format",
                        "csv",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            writer.assert_called_once_with(data, report, output)


if __name__ == "__main__":
    unittest.main()
