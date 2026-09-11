from __future__ import annotations

from pathlib import Path


def prepare_output_root(output_dir: str | Path, *, label: str) -> Path:
    """Prepare a publication parent while rejecting a symlinked output leaf."""
    output = Path(output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise ValueError(f"{label} output path is a disallowed symlink: {output}")
    if output.exists() and not output.is_dir():
        raise ValueError(f"{label} output path is not a directory: {output}")
    return output
