from __future__ import annotations

import re

_KTU_RE = re.compile(r"^(?:KTU\s+)?(\d+\.\d+(?:[A-Za-z])?)$", re.IGNORECASE)


def normalize_cuc_tablet(value: str) -> str:
    """Return CUC's canonical ``KTU N.N`` spelling for an exact KTU id."""
    text = " ".join((value or "").split())
    match = _KTU_RE.fullmatch(text)
    return f"KTU {match.group(1)}" if match else ""
