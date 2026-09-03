#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fetch and prepare the thesis source files the parsers read.

Both source files are open-access deposits of the same thesis in the White Rose
eTheses repository:

> Burns, Duncan Coe (2003). *Contents, texts and contexts: a contextualist
> approach to the Ugaritic texts and their cultic vocabulary.* PhD thesis,
> University of Sheffield. <https://etheses.whiterose.ac.uk/id/eprint/15038/>

Neither is tracked in git (they are large, and the source is © the author), so
each parser calls ``ensure()`` to put its input in place before parsing. The
call is idempotent: it does nothing when the input is already there, and it
verifies a pinned SHA-256 on everything it downloads, so a truncated or
substituted file is rejected rather than silently parsed.

Run directly to fetch both without parsing:

    uv run --no-project scripts/sources.py
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNK = 1 << 16


@dataclass(frozen=True)
class Source:
    """One downloadable input.

    ``target`` is what the parser reads, relative to the project root: a file
    for a plain download, a directory for an archive that is unpacked into it.
    """

    name: str
    url: str
    sha256: str
    size: int
    target: str
    archive: bool = False

    def path(self, root: Path) -> Path:
        return root / self.target


APPENDIX = Source(
    name="Appendix",
    url="https://etheses.whiterose.ac.uk/id/eprint/15038/3/Appendix.pdf",
    sha256="a7bc936612c0b954f1ed0c3cb89c56631d4cc9116ffa7a45d8f5deb13b5492c2",
    size=1_056_818,
    target="Appendix.pdf",
)

WORKBOOKS = Source(
    name="Workbooks",
    url="https://etheses.whiterose.ac.uk/id/eprint/15038/4/Workbooks.zip",
    sha256="4f90bf6f01d59a0fd71da9af57c8e64adc886aa32f8bf81b7d4426316b3e5d29",
    size=4_868_771,
    target="Workbooks",
    archive=True,
)

SOURCES = (APPENDIX, WORKBOOKS)


class SourceError(RuntimeError):
    """The input is absent and could not be prepared."""


def _download(source: Source, destination: Path) -> None:
    print(
        f"Downloading {source.name} ({source.size / 1e6:.1f} MB) from {source.url}",
        file=sys.stderr,
    )
    digest = hashlib.sha256()
    with urllib.request.urlopen(source.url) as response, destination.open("wb") as out:
        while chunk := response.read(CHUNK):
            digest.update(chunk)
            out.write(chunk)
    actual = digest.hexdigest()
    if actual != source.sha256:
        raise SourceError(
            f"{source.name}: checksum mismatch — the download does not match the "
            f"pinned copy of this deposit.\n"
            f"  expected {source.sha256}\n  got      {actual}"
        )


def _extract(archive_path: Path, destination: Path, report_as: Path | None = None) -> int:
    """Unpack a zip, refusing members that would escape the destination."""
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()
        for member in members:
            resolved = (destination / member).resolve()
            if not resolved.is_relative_to(destination.resolve()):
                raise SourceError(f"archive member escapes the target: {member!r}")
        archive.extractall(destination)
    pdfs = sum(1 for member in members if member.lower().endswith(".pdf"))
    print(f"Extracted {pdfs} PDFs into {report_as or destination}", file=sys.stderr)
    return pdfs


def ensure(source: Source, root: Path = PROJECT_ROOT, download: bool = True) -> Path:
    """Return the path to ``source``'s input, fetching it if it is not there."""
    target = source.path(root)
    if target.exists():
        return target
    if not download:
        raise SourceError(
            f"{target} is missing. Re-run without --no-download to fetch it from "
            f"{source.url}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    # Download beside the target and move into place only once the checksum is
    # good, so an interrupted run never leaves a half-written input behind.
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        staged = Path(tmp) / "download"
        _download(source, staged)
        if source.archive:
            unpacked = Path(tmp) / "unpacked"
            unpacked.mkdir()
            _extract(staged, unpacked, report_as=target)
            shutil.move(str(unpacked), str(target))
        else:
            shutil.move(str(staged), str(target))
    return target


def main() -> int:
    for source in SOURCES:
        path = ensure(source)
        print(f"{source.name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
