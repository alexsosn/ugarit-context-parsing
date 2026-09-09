from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Iterable

from .source import WorkbookRecord


class BurnsNormalizationError(ValueError):
    """Raised when source-domain provenance cannot be normalized safely."""


class BurnsTextualStatus(str, Enum):
    TEXTUAL = "textual"
    NON_TEXTUAL_NOT_ATTESTED = "non_textual_not_attested"


class BurnsSemanticStatus(str, Enum):
    POSITIVE_FIXED = "positive_fixed"
    PROBABLE_CULTIC = "probable_cultic"
    NO_SECURE_CULTIC = "no_secure_cultic"
    HOMOGRAPH_EXCLUDED = "homograph_excluded"
    UNSUPPORTED = "unsupported"


class BurnsInterpretiveStatus(str, Enum):
    # Burns comments are preserved verbatim. This slice deliberately does not
    # turn punctuation/prose heuristics into scholarly interpretation labels.
    UNSPECIFIED = "unspecified"


class BurnsWorksheetRole(str, Enum):
    PRIME_GP = "prime_gp"
    PRIME_PH = "prime_ph"
    DERIVED_COMMON = "derived_common"
    DERIVED_GP_ONLY = "derived_gp_only"
    DERIVED_PH_ONLY = "derived_ph_only"


@dataclass(frozen=True)
class BurnsSourceRecord:
    record_id: str
    source_file: str
    source_row: int
    source_page: int
    section: str
    root: str
    headword: str
    ktu: str
    references: str
    locus: str
    room: str
    point: str
    depth: str
    disputed: str
    comments: str
    worksheet_id: str
    workbook_number: int
    workbook_label: str
    worksheet_number: int
    worksheet_role: BurnsWorksheetRole
    textual_status: BurnsTextualStatus
    semantic_status: BurnsSemanticStatus
    interpretive_status: BurnsInterpretiveStatus


@dataclass(frozen=True)
class BurnsAnnotation:
    annotation_id: str
    worksheet_id: str
    workbook_number: int
    workbook_label: str
    worksheet_number: int
    worksheet_role: BurnsWorksheetRole
    first_source_row: int
    section: str
    root: str
    headword: str
    ktu: str
    references: str
    textual_status: BurnsTextualStatus
    semantic_status: BurnsSemanticStatus
    interpretive_status: BurnsInterpretiveStatus
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class NormalizedBurnsSource:
    records: tuple[BurnsSourceRecord, ...]
    annotations: tuple[BurnsAnnotation, ...]


_WORKBOOK_RE = re.compile(r"^(0[1-9])(?:\s|$)")
_WORKSHEET_RE = re.compile(r"^Worksheet\s+([1-5])$", re.IGNORECASE)
_WORKSHEET_ROLES = {
    1: BurnsWorksheetRole.PRIME_GP,
    2: BurnsWorksheetRole.PRIME_PH,
    3: BurnsWorksheetRole.DERIVED_COMMON,
    4: BurnsWorksheetRole.DERIVED_GP_ONLY,
    5: BurnsWorksheetRole.DERIVED_PH_ONLY,
}


def _worksheet_provenance(
    source_file: str,
) -> tuple[str, int, str, int, BurnsWorksheetRole]:
    if not source_file or "\\" in source_file:
        raise BurnsNormalizationError(
            f"source_file must be a POSIX relative Workbook path: {source_file!r}"
        )
    raw_parts = source_file.split("/")
    if source_file.startswith("/") or any(part in {"", ".", ".."} for part in raw_parts):
        raise BurnsNormalizationError(
            f"source_file must be a safe relative Workbook path: {source_file!r}"
        )

    path = PurePosixPath(source_file)
    parts = path.parts
    if len(parts) < 2:
        raise BurnsNormalizationError(
            f"source_file must include a workbook directory and worksheet file: {source_file!r}"
        )

    workbook_label = parts[0]
    workbook_match = _WORKBOOK_RE.match(workbook_label)
    if workbook_match is None:
        raise BurnsNormalizationError(
            f"source_file has unsupported workbook directory: {workbook_label!r}"
        )
    workbook_number = int(workbook_match.group(1))

    suffix = path.suffix
    if suffix.casefold() not in {".csv", ".pdf"}:
        raise BurnsNormalizationError(
            f"source_file must end in .csv or .pdf: {source_file!r}"
        )
    stem = path.name[: -len(suffix)]
    worksheet_match = _WORKSHEET_RE.fullmatch(stem)
    if worksheet_match is None:
        raise BurnsNormalizationError(
            f"source_file has unsupported worksheet filename: {path.name!r}"
        )
    worksheet_number = int(worksheet_match.group(1))

    worksheet_id = "/".join((*parts[:-1], stem))
    return (
        worksheet_id,
        workbook_number,
        workbook_label,
        worksheet_number,
        _WORKSHEET_ROLES[worksheet_number],
    )


def _nfc_payload(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {str(key): _nfc_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_nfc_payload(item) for item in value]
    return value


def _stable_id(prefix: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        _nfc_payload(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{prefix}{hashlib.sha256(canonical).hexdigest()}"


def _semantic_status(workbook_number: int, section: str) -> BurnsSemanticStatus:
    if 1 <= workbook_number <= 4:
        if section == "Section α":
            return BurnsSemanticStatus.POSITIVE_FIXED
        if section == "Section β":
            return BurnsSemanticStatus.HOMOGRAPH_EXCLUDED
        return BurnsSemanticStatus.UNSUPPORTED

    if 5 <= workbook_number <= 9:
        if section == "Section α1":
            return BurnsSemanticStatus.PROBABLE_CULTIC
        if section == "Section α2":
            return BurnsSemanticStatus.NO_SECURE_CULTIC
        if section == "Section β":
            return BurnsSemanticStatus.HOMOGRAPH_EXCLUDED
        return BurnsSemanticStatus.UNSUPPORTED

    return BurnsSemanticStatus.UNSUPPORTED


def _textual_status(ktu: str) -> BurnsTextualStatus:
    if ktu.startswith("Not attested"):
        return BurnsTextualStatus.NON_TEXTUAL_NOT_ATTESTED
    return BurnsTextualStatus.TEXTUAL


def _normalize_record(record: WorkbookRecord) -> BurnsSourceRecord:
    if record.source_row < 1:
        raise BurnsNormalizationError("source_row must be an integer >= 1")
    if record.source_page < 1:
        raise BurnsNormalizationError("source_page must be an integer >= 1")

    (
        worksheet_id,
        workbook_number,
        workbook_label,
        worksheet_number,
        worksheet_role,
    ) = _worksheet_provenance(record.source_file)

    payload: dict[str, object] = {
        "schema": "burns-source-record-v1",
        "worksheet_id": worksheet_id,
        "source_row": record.source_row,
        "source_page": record.source_page,
        "section": record.section,
        "root": record.root,
        "headword": record.headword,
        "ktu": record.ktu,
        "references": record.references,
        "locus": record.locus,
        "room": record.room,
        "point": record.point,
        "depth": record.depth,
        "disputed": record.disputed,
        "comments": record.comments,
    }
    record_id = _stable_id("burns-record-sha256:", payload)

    return BurnsSourceRecord(
        record_id=record_id,
        source_file=record.source_file,
        source_row=record.source_row,
        source_page=record.source_page,
        section=record.section,
        root=record.root,
        headword=record.headword,
        ktu=record.ktu,
        references=record.references,
        locus=record.locus,
        room=record.room,
        point=record.point,
        depth=record.depth,
        disputed=record.disputed,
        comments=record.comments,
        worksheet_id=worksheet_id,
        workbook_number=workbook_number,
        workbook_label=workbook_label,
        worksheet_number=worksheet_number,
        worksheet_role=worksheet_role,
        textual_status=_textual_status(record.ktu),
        semantic_status=_semantic_status(workbook_number, record.section),
        interpretive_status=BurnsInterpretiveStatus.UNSPECIFIED,
    )


def _annotation_key(record: BurnsSourceRecord) -> tuple[str, str, str, str, str, str]:
    return (
        record.worksheet_id,
        record.section,
        record.root,
        record.headword,
        record.ktu,
        record.references,
    )


def _build_annotation(records: list[BurnsSourceRecord]) -> BurnsAnnotation:
    first = records[0]
    payload: dict[str, object] = {
        "schema": "burns-annotation-v1",
        "worksheet_id": first.worksheet_id,
        "first_source_row": first.source_row,
        "section": first.section,
        "root": first.root,
        "headword": first.headword,
        "ktu": first.ktu,
        "references": first.references,
    }
    return BurnsAnnotation(
        annotation_id=_stable_id("burns-annotation-sha256:", payload),
        worksheet_id=first.worksheet_id,
        workbook_number=first.workbook_number,
        workbook_label=first.workbook_label,
        worksheet_number=first.worksheet_number,
        worksheet_role=first.worksheet_role,
        first_source_row=first.source_row,
        section=first.section,
        root=first.root,
        headword=first.headword,
        ktu=first.ktu,
        references=first.references,
        textual_status=first.textual_status,
        semantic_status=first.semantic_status,
        interpretive_status=first.interpretive_status,
        record_ids=tuple(record.record_id for record in records),
    )


def normalize_workbook_records(
    records: Iterable[WorkbookRecord],
) -> NormalizedBurnsSource:
    normalized: list[BurnsSourceRecord] = []
    seen_record_ids: set[str] = set()
    last_row_by_worksheet: dict[str, int] = {}

    for source_record in records:
        record = _normalize_record(source_record)
        if record.record_id in seen_record_ids:
            raise BurnsNormalizationError(
                f"duplicate normalized source record: {record.record_id}"
            )
        seen_record_ids.add(record.record_id)

        prior_row = last_row_by_worksheet.get(record.worksheet_id)
        if prior_row is not None and record.source_row <= prior_row:
            raise BurnsNormalizationError(
                "source row order must be strictly monotonic within one worksheet: "
                f"{record.worksheet_id!r} row {record.source_row} follows {prior_row}"
            )
        last_row_by_worksheet[record.worksheet_id] = record.source_row
        normalized.append(record)

    annotations: list[BurnsAnnotation] = []
    current: list[BurnsSourceRecord] = []
    previous: BurnsSourceRecord | None = None

    for record in normalized:
        can_extend = (
            previous is not None
            and _annotation_key(record) == _annotation_key(previous)
            and record.source_row == previous.source_row + 1
        )
        if current and not can_extend:
            annotations.append(_build_annotation(current))
            current = []
        current.append(record)
        previous = record

    if current:
        annotations.append(_build_annotation(current))

    return NormalizedBurnsSource(
        records=tuple(normalized),
        annotations=tuple(annotations),
    )
