"""Exact-value CSV/XLSX reader shared by all source adapters."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath
from xml.etree import ElementTree

from core.vericlose.ingestion.contracts import SourceDocument, SourceFormat


class TabularReadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class TabularRow:
    table_name: str
    row_number: int
    values: tuple[tuple[str, str], ...]
    raw_row_hash: str

    def get(self, column: str) -> str:
        return dict(self.values).get(column, "")


@dataclass(frozen=True, slots=True)
class TabularData:
    source_format: SourceFormat
    table_name: str
    headers: tuple[str, ...]
    rows: tuple[TabularRow, ...]


def read_tabular(document: SourceDocument) -> TabularData:
    if document.extension == ".csv":
        return _read_csv(document)
    if document.extension == ".xlsx":
        return _read_xlsx(document)
    raise TabularReadError("UNSUPPORTED_FILE_FORMAT", "Only CSV and XLSX files are supported")


def detect_format(document: SourceDocument) -> SourceFormat:
    if document.extension == ".csv":
        return SourceFormat.CSV
    if document.extension == ".xlsx":
        return SourceFormat.XLSX
    return SourceFormat.UNKNOWN


def _read_csv(document: SourceDocument) -> TabularData:
    try:
        text = document.content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise TabularReadError("CSV_ENCODING_INVALID", "CSV must be UTF-8 encoded") from error
    try:
        reader = csv.reader(io.StringIO(text), strict=True)
        header_row = next(reader, None)
        if header_row is None:
            raise TabularReadError("EMPTY_FILE", "The uploaded CSV is empty")
        headers = tuple(cell.strip() for cell in header_row)
        _validate_headers(headers)
        rows: list[TabularRow] = []
        for row_number, cells in enumerate(reader, start=2):
            if not cells or all(not cell.strip() for cell in cells):
                continue
            if len(cells) != len(headers):
                raise TabularReadError(
                    "CSV_COLUMN_COUNT_MISMATCH",
                    f"Row {row_number} has {len(cells)} cells; expected {len(headers)}",
                )
            values = tuple(zip(headers, cells, strict=True))
            rows.append(_tabular_row("rows", row_number, values))
    except csv.Error as error:
        raise TabularReadError("CSV_MALFORMED", str(error)) from error
    return TabularData(SourceFormat.CSV, "rows", headers, tuple(rows))


def _read_xlsx(document: SourceDocument) -> TabularData:
    try:
        with zipfile.ZipFile(io.BytesIO(document.content)) as archive:
            table_name, sheet_path = _first_sheet(archive)
            shared_strings = _shared_strings(archive)
            date_styles = _date_style_indexes(archive)
            sheet = ElementTree.fromstring(archive.read(sheet_path))
    except (
        zipfile.BadZipFile,
        KeyError,
        ElementTree.ParseError,
        StopIteration,
        ValueError,
    ) as error:
        raise TabularReadError("XLSX_MALFORMED", "The workbook could not be opened") from error
    sheet_rows = sheet.findall(f".//{{{_MAIN_NS}}}sheetData/{{{_MAIN_NS}}}row")
    if not sheet_rows:
        raise TabularReadError("EMPTY_FILE", "The first worksheet is empty")
    header_cells = _xlsx_row_values(sheet_rows[0], shared_strings, date_styles)
    if not header_cells:
        raise TabularReadError("HEADER_MISSING", "A non-empty header row is required")
    width = max(header_cells) + 1
    headers = tuple(header_cells.get(index, "").strip() for index in range(width))
    _validate_headers(headers)
    rows: list[TabularRow] = []
    for ordinal, xml_row in enumerate(sheet_rows[1:], start=2):
        row_number = int(xml_row.attrib.get("r", ordinal))
        cells = _xlsx_row_values(xml_row, shared_strings, date_styles)
        normalized = tuple(cells.get(index, "") for index in range(len(headers)))
        if all(not value.strip() for value in normalized):
            continue
        values = tuple(zip(headers, normalized, strict=True))
        rows.append(_tabular_row(table_name, row_number, values))
    return TabularData(SourceFormat.XLSX, table_name, headers, tuple(rows))


def _validate_headers(headers: tuple[str, ...]) -> None:
    if not headers or all(not header for header in headers):
        raise TabularReadError("HEADER_MISSING", "A non-empty header row is required")
    if any(not header for header in headers):
        raise TabularReadError("HEADER_BLANK", "Header names cannot be blank")
    normalized = [header.casefold() for header in headers]
    if len(set(normalized)) != len(normalized):
        raise TabularReadError("HEADER_DUPLICATE", "Header names must be unique")


def _tabular_row(
    table_name: str,
    row_number: int,
    values: tuple[tuple[str, str], ...],
) -> TabularRow:
    raw = json.dumps(dict(values), sort_keys=True, separators=(",", ":")).encode()
    return TabularRow(table_name, row_number, values, hashlib.sha256(raw).hexdigest())


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CELL_REFERENCE = re.compile(r"^([A-Z]+)[0-9]+$")
_BUILTIN_DATE_FORMATS = frozenset({14, 15, 16, 17, 18, 19, 20, 21, 22, 45, 46, 47})


def _first_sheet(archive: zipfile.ZipFile) -> tuple[str, str]:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    sheet = workbook.find(f".//{{{_MAIN_NS}}}sheet")
    if sheet is None:
        raise ValueError("workbook has no sheets")
    relationship_id = sheet.attrib[f"{{{_REL_NS}}}id"]
    relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship = next(
        item
        for item in relationships.findall(f"{{{_PACKAGE_REL_NS}}}Relationship")
        if item.attrib.get("Id") == relationship_id
    )
    target = relationship.attrib["Target"].lstrip("/")
    path = target if target.startswith("xl/") else str(PurePosixPath("xl") / target)
    return sheet.attrib.get("name", "Sheet1"), path


def _shared_strings(archive: zipfile.ZipFile) -> tuple[str, ...]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return ()
    return tuple(
        "".join(node.text or "" for node in item.findall(f".//{{{_MAIN_NS}}}t"))
        for item in root.findall(f"{{{_MAIN_NS}}}si")
    )


def _date_style_indexes(archive: zipfile.ZipFile) -> frozenset[int]:
    try:
        root = ElementTree.fromstring(archive.read("xl/styles.xml"))
    except KeyError:
        return frozenset()
    custom_formats = {
        int(item.attrib["numFmtId"]): item.attrib.get("formatCode", "")
        for item in root.findall(f".//{{{_MAIN_NS}}}numFmt")
    }
    cell_formats = root.find(f"{{{_MAIN_NS}}}cellXfs")
    if cell_formats is None:
        return frozenset()
    indexes: set[int] = set()
    for index, item in enumerate(cell_formats.findall(f"{{{_MAIN_NS}}}xf")):
        format_id = int(item.attrib.get("numFmtId", "0"))
        custom = custom_formats.get(format_id, "").lower()
        if format_id in _BUILTIN_DATE_FORMATS or ("y" in custom and "d" in custom):
            indexes.add(index)
    return frozenset(indexes)


def _xlsx_row_values(
    row: ElementTree.Element,
    shared_strings: tuple[str, ...],
    date_styles: frozenset[int],
) -> dict[int, str]:
    values: dict[int, str] = {}
    for cell in row.findall(f"{{{_MAIN_NS}}}c"):
        reference = cell.attrib.get("r", "")
        match = _CELL_REFERENCE.match(reference)
        if match is None:
            continue
        column = _column_index(match.group(1))
        cell_type = cell.attrib.get("t", "n")
        if cell_type == "inlineStr":
            value = "".join(node.text or "" for node in cell.findall(f".//{{{_MAIN_NS}}}t"))
        else:
            value_node = cell.find(f"{{{_MAIN_NS}}}v")
            raw = value_node.text if value_node is not None and value_node.text else ""
            if cell_type == "s" and raw:
                value = shared_strings[int(raw)]
            elif cell_type == "b":
                value = "TRUE" if raw == "1" else "FALSE"
            else:
                value = raw
        style_index = int(cell.attrib.get("s", "0"))
        if value and style_index in date_styles and cell_type == "n":
            value = _excel_date_text(value)
        values[column] = value
    return values


def _column_index(letters: str) -> int:
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def _excel_date_text(raw: str) -> str:
    try:
        serial = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError("invalid Excel date serial") from error
    whole_days = int(serial)
    fraction = serial - Decimal(whole_days)
    microseconds = int(fraction * Decimal(86_400_000_000))
    parsed = datetime(1899, 12, 30, tzinfo=UTC) + timedelta(
        days=whole_days,
        microseconds=microseconds,
    )
    return parsed.date().isoformat() if not fraction else parsed.isoformat()
