"""Versioned, declarative mapping profiles with a closed transform allowlist."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml

from core.vericlose.domain.enums import SourceType
from core.vericlose.ingestion.contracts import MappingProfileRef, SourceFormat


class MappingConfigurationError(ValueError):
    """Raised when a checked-in mapping profile is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class FieldMapping:
    canonical_field: str
    aliases: tuple[str, ...]
    required: bool
    transform: str

    def __post_init__(self) -> None:
        if not self.canonical_field.strip():
            raise MappingConfigurationError("canonical_field cannot be blank")
        if not self.aliases or any(not alias.strip() for alias in self.aliases):
            raise MappingConfigurationError(f"{self.canonical_field} requires non-blank aliases")
        if len(set(self.aliases)) != len(self.aliases):
            raise MappingConfigurationError(f"{self.canonical_field} aliases must be unique")
        if self.transform not in SAFE_TRANSFORMS:
            raise MappingConfigurationError(
                f"unsafe transform {self.transform!r} for {self.canonical_field}"
            )


@dataclass(frozen=True, slots=True)
class FileMappingProfile:
    """One source layout; `bind` resolves aliases against an actual header."""

    ref: MappingProfileRef
    supported_formats: frozenset[SourceFormat]
    fields: tuple[FieldMapping, ...]
    resolved_columns: tuple[tuple[str, str], ...] = ()
    is_bound: bool = False

    def __post_init__(self) -> None:
        names = [field.canonical_field for field in self.fields]
        if not self.fields or any(not isinstance(field, FieldMapping) for field in self.fields):
            raise MappingConfigurationError("profiles require typed field mappings")
        if len(set(names)) != len(names):
            raise MappingConfigurationError("canonical fields must be unique within a profile")
        if not any(field.required for field in self.fields):
            raise MappingConfigurationError("profiles require at least one required field")
        if not self.supported_formats or SourceFormat.UNKNOWN in self.supported_formats:
            raise MappingConfigurationError("mapping profiles require concrete supported formats")

    def bind(self, headers: tuple[str, ...]) -> FileMappingProfile:
        normalized = {header.strip().casefold(): header for header in headers}
        resolved: list[tuple[str, str]] = []
        for field in self.fields:
            source_column = next(
                (
                    normalized[alias.strip().casefold()]
                    for alias in field.aliases
                    if alias.strip().casefold() in normalized
                ),
                None,
            )
            if source_column is not None:
                resolved.append((field.canonical_field, source_column))
        return replace(self, resolved_columns=tuple(resolved), is_bound=True)

    def source_column_for(self, canonical_field: str) -> str | None:
        resolved = dict(self.resolved_columns)
        if self.is_bound:
            return resolved.get(canonical_field)
        field = next(
            (item for item in self.fields if item.canonical_field == canonical_field),
            None,
        )
        return field.aliases[0] if field is not None else None

    def transform_for(self, canonical_field: str) -> str | None:
        field = next(
            (item for item in self.fields if item.canonical_field == canonical_field),
            None,
        )
        return field.transform if field is not None else None

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(field.canonical_field for field in self.fields if field.required)

    def match_score_bps(self, headers: tuple[str, ...]) -> int:
        if not headers or not self.fields:
            return 0
        bound = self.bind(headers)
        resolved = dict(bound.resolved_columns)
        required = [field for field in self.fields if field.required]
        if any(field.canonical_field not in resolved for field in required):
            return 0
        required_weight = 8_000
        optional_weight = 2_000
        required_score = required_weight if required else 0
        optional = [field for field in self.fields if not field.required]
        optional_matches = sum(field.canonical_field in resolved for field in optional)
        optional_score = (
            optional_weight if not optional else optional_weight * optional_matches // len(optional)
        )
        return min(10_000, required_score + optional_score)


class MappingCatalog:
    """Validated in-memory catalog loaded only from declarative YAML."""

    def __init__(self, profiles: tuple[FileMappingProfile, ...]) -> None:
        identities = [profile.ref.versioned_id for profile in profiles]
        if len(set(identities)) != len(identities):
            raise MappingConfigurationError("mapping profile identities must be unique")
        self._profiles = profiles

    @property
    def profiles(self) -> tuple[FileMappingProfile, ...]:
        return self._profiles

    def for_source(self, source_type: SourceType) -> tuple[FileMappingProfile, ...]:
        return tuple(
            profile for profile in self._profiles if profile.ref.source_type is source_type
        )

    def get(self, versioned_id: str) -> FileMappingProfile:
        try:
            return next(
                profile for profile in self._profiles if profile.ref.versioned_id == versioned_id
            )
        except StopIteration as error:
            raise KeyError(versioned_id) from error

    @classmethod
    def from_directory(cls, directory: Path) -> MappingCatalog:
        profiles: list[FileMappingProfile] = []
        for path in sorted(directory.glob("*.yaml")):
            profiles.extend(
                _profiles_from_payload(yaml.safe_load(path.read_text(encoding="utf-8")), path)
            )
        if not profiles:
            raise MappingConfigurationError(f"no mapping profiles found under {directory}")
        return cls(tuple(profiles))


def _profiles_from_payload(payload: Any, path: Path) -> tuple[FileMappingProfile, ...]:
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise MappingConfigurationError(f"{path}: expected mapping schema_version 1.0")
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise MappingConfigurationError(f"{path}: profiles must be a non-empty list")
    profiles: list[FileMappingProfile] = []
    for raw in raw_profiles:
        if not isinstance(raw, dict) or not isinstance(raw.get("fields"), dict):
            raise MappingConfigurationError(f"{path}: malformed profile")
        if not isinstance(raw.get("formats"), list) or not raw["formats"]:
            raise MappingConfigurationError(f"{path}: formats must be a non-empty list")
        if any(not isinstance(specification, dict) for specification in raw["fields"].values()):
            raise MappingConfigurationError(f"{path}: every field mapping must be an object")
        try:
            source_type = SourceType(str(raw["source_type"]).upper())
            supported_formats = frozenset(
                SourceFormat(str(value).upper()) for value in raw["formats"]
            )
            ref = MappingProfileRef(str(raw["profile_id"]), str(raw["version"]), source_type)
        except (KeyError, ValueError, TypeError) as error:
            raise MappingConfigurationError(f"{path}: invalid profile identity") from error
        fields: list[FieldMapping] = []
        for canonical, specification in raw["fields"].items():
            required = specification.get("required", False)
            aliases = specification.get("aliases", ())
            if not isinstance(required, bool) or not isinstance(aliases, list):
                raise MappingConfigurationError(
                    f"{path}: required must be boolean and aliases must be a list"
                )
            fields.append(
                FieldMapping(
                    canonical_field=str(canonical),
                    aliases=tuple(str(alias) for alias in aliases),
                    required=required,
                    transform=str(specification.get("transform", "strip")),
                )
            )
        profiles.append(FileMappingProfile(ref, supported_formats, tuple(fields)))
    return tuple(profiles)


def apply_transform(name: str, raw_value: str) -> str | int | date | datetime:
    """Apply one reviewed transform; configuration cannot execute arbitrary code."""

    try:
        transform = SAFE_TRANSFORMS[name]
    except KeyError as error:
        raise MappingConfigurationError(f"unknown safe transform: {name}") from error
    return transform(raw_value)


def parse_minor_units(raw_value: str) -> int:
    value = raw_value.strip()
    if not value or any(character not in "+-0123456789" for character in value):
        raise ValueError("expected a signed integer in minor units")
    return int(value)


def parse_decimal_minor(raw_value: str) -> int:
    value = raw_value.strip().replace(",", "")
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("expected a decimal amount") from error
    if not amount.is_finite() or amount.as_tuple().exponent < -2:
        raise ValueError("amount cannot have more than two decimal places")
    minor = amount * 100
    if minor != minor.to_integral_value():
        raise ValueError("amount cannot contain fractional minor units")
    return int(minor)


def parse_iso_datetime(raw_value: str) -> datetime:
    parsed = datetime.fromisoformat(raw_value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def parse_iso_date(raw_value: str) -> date:
    return date.fromisoformat(raw_value.strip())


def parse_excel_datetime(raw_value: str) -> datetime:
    """Convert an exact Excel serial string without using binary floating point."""

    try:
        serial = Decimal(raw_value)
    except InvalidOperation as error:
        raise ValueError("invalid Excel date serial") from error
    days = int(serial)
    seconds = int((serial - Decimal(days)) * Decimal(86_400))
    return datetime(1899, 12, 30, tzinfo=UTC) + timedelta(days=days, seconds=seconds)


SAFE_TRANSFORMS = {
    "strip": lambda value: value.strip(),
    "upper": lambda value: value.strip().upper(),
    "integer": lambda value: int(value.strip()),
    "minor_units": parse_minor_units,
    "decimal_minor": parse_decimal_minor,
    "iso_datetime": parse_iso_datetime,
    "iso_date": parse_iso_date,
}
