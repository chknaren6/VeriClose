"""Validated, versioned finance policy consumed by deterministic rules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from core.vericlose.domain.enums import (
    ActionType,
    Direction,
    EventType,
    ExceptionCategory,
    Severity,
)


@dataclass(frozen=True, slots=True)
class DatePolicy:
    settlement_to_bank_min_days: int
    settlement_to_bank_max_days: int
    bank_to_erp_max_days: int


@dataclass(frozen=True, slots=True)
class AccountRolePolicy:
    account_codes: frozenset[str]
    direction: Direction


@dataclass(frozen=True, slots=True)
class GroupingPolicy:
    max_candidates: int
    max_group_size: int
    max_valid_groups: int


@dataclass(frozen=True, slots=True)
class ExceptionPolicy:
    category: ExceptionCategory
    severity: Severity
    action: ActionType
    requires_company_input: bool


@dataclass(frozen=True, slots=True)
class ReconciliationPolicy:
    schema_version: str
    policy_id: str
    version: str
    currency: str
    dates: DatePolicy
    tolerances_minor: Mapping[str, int]
    component_signs: Mapping[str, int]
    account_roles: Mapping[str, AccountRolePolicy]
    grouping: GroupingPolicy
    auto_clear_enabled: bool
    auto_clear_required_checks: frozenset[str]
    support_scoring_bps: Mapping[str, int]
    exceptions: Mapping[str, ExceptionPolicy]

    @property
    def versioned_id(self) -> str:
        return f"{self.policy_id}@{self.version}"

    def tolerance(self, name: str) -> int:
        try:
            return self.tolerances_minor[name]
        except KeyError as error:
            raise KeyError(f"unknown tolerance: {name}") from error

    def component_sign(self, event_type: EventType, direction: Direction) -> int:
        key = (
            f"ADJUSTMENT_{direction.value}"
            if event_type is EventType.ADJUSTMENT
            else event_type.value
        )
        try:
            return self.component_signs[key]
        except KeyError as error:
            raise KeyError(f"component sign is not configured for {key}") from error

    def role(self, name: str) -> AccountRolePolicy:
        try:
            return self.account_roles[name]
        except KeyError as error:
            raise KeyError(f"unknown account role: {name}") from error

    def exception(self, reason_code: str) -> ExceptionPolicy:
        return self.exceptions.get(reason_code, self.exceptions["UNKNOWN_UNRESOLVED"])


def load_policy(path: Path) -> ReconciliationPolicy:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(payload, "policy root")
    _require_keys(
        root,
        {
            "schema_version",
            "policy_id",
            "version",
            "currency",
            "dates",
            "tolerances_minor",
            "component_signs",
            "account_roles",
            "grouping",
            "auto_clear",
            "support_scoring_bps",
            "exceptions",
        },
        "policy root",
    )
    if str(root["schema_version"]) != "1.0":
        raise ValueError("unsupported policy schema_version")
    currency = str(root["currency"]).upper()
    if currency != "INR":
        raise ValueError("the frozen MVP policy must use INR")

    dates = _int_mapping(root["dates"], "dates")
    tolerances = _int_mapping(root["tolerances_minor"], "tolerances_minor")
    signs = _int_mapping(root["component_signs"], "component_signs")
    grouping = _int_mapping(root["grouping"], "grouping")
    scoring = _int_mapping(root["support_scoring_bps"], "support_scoring_bps")
    if any(value < 0 for value in tolerances.values()):
        raise ValueError("amount tolerances cannot be negative")
    if set(signs.values()) - {-1, 1}:
        raise ValueError("component signs must be -1 or 1")
    if sum(scoring.values()) != 10_000:
        raise ValueError("support scoring weights must total 10000 bps")

    roles: dict[str, AccountRolePolicy] = {}
    for name, raw in _mapping(root["account_roles"], "account_roles").items():
        role = _mapping(raw, f"account_roles.{name}")
        codes = role.get("account_codes")
        if (
            not isinstance(codes, list)
            or not codes
            or any(not isinstance(code, str) or not code.strip() for code in codes)
        ):
            raise ValueError(f"account_roles.{name}.account_codes must be non-empty strings")
        roles[str(name)] = AccountRolePolicy(frozenset(codes), Direction(role["direction"]))
    if set(roles) != {"bank", "clearing", "fee", "tax"}:
        raise ValueError("account_roles must define bank, clearing, fee, and tax")

    auto_clear = _mapping(root["auto_clear"], "auto_clear")
    enabled = auto_clear.get("enabled")
    required_checks = auto_clear.get("required_checks")
    if not isinstance(enabled, bool):
        raise TypeError("auto_clear.enabled must be a boolean")
    if not isinstance(required_checks, list) or not required_checks:
        raise ValueError("auto_clear.required_checks must be non-empty")

    exceptions: dict[str, ExceptionPolicy] = {}
    for code, raw in _mapping(root["exceptions"], "exceptions").items():
        item = _mapping(raw, f"exceptions.{code}")
        company_input = item.get("requires_company_input")
        if not isinstance(company_input, bool):
            raise TypeError(f"exceptions.{code}.requires_company_input must be boolean")
        exceptions[str(code)] = ExceptionPolicy(
            ExceptionCategory(item["category"]),
            Severity(item["severity"]),
            ActionType(item["action"]),
            company_input,
        )
    if "UNKNOWN_UNRESOLVED" not in exceptions:
        raise ValueError("policy requires UNKNOWN_UNRESOLVED fallback")

    result = ReconciliationPolicy(
        schema_version="1.0",
        policy_id=_text(root["policy_id"], "policy_id"),
        version=_text(root["version"], "version"),
        currency=currency,
        dates=DatePolicy(
            dates["settlement_to_bank_min_days"],
            dates["settlement_to_bank_max_days"],
            dates["bank_to_erp_max_days"],
        ),
        tolerances_minor=MappingProxyType(tolerances),
        component_signs=MappingProxyType(signs),
        account_roles=MappingProxyType(roles),
        grouping=GroupingPolicy(
            grouping["max_candidates"],
            grouping["max_group_size"],
            grouping["max_valid_groups"],
        ),
        auto_clear_enabled=enabled,
        auto_clear_required_checks=frozenset(str(code) for code in required_checks),
        support_scoring_bps=MappingProxyType(scoring),
        exceptions=MappingProxyType(exceptions),
    )
    _validate_ranges(result)
    return result


def _validate_ranges(policy: ReconciliationPolicy) -> None:
    if policy.dates.settlement_to_bank_min_days < 0:
        raise ValueError("settlement_to_bank_min_days cannot be negative")
    if policy.dates.settlement_to_bank_max_days < policy.dates.settlement_to_bank_min_days:
        raise ValueError("settlement bank date range is inverted")
    if policy.grouping.max_candidates < 1 or policy.grouping.max_group_size < 1:
        raise ValueError("grouping bounds must be positive")
    if policy.grouping.max_group_size > policy.grouping.max_candidates:
        raise ValueError("max_group_size cannot exceed max_candidates")
    if policy.grouping.max_valid_groups < 2:
        raise ValueError("max_valid_groups must permit ambiguity detection")


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise TypeError(f"{name} must be a string-keyed mapping")
    return value


def _int_mapping(value: object, name: str) -> dict[str, int]:
    result = _mapping(value, name)
    if any(isinstance(item, bool) or not isinstance(item, int) for item in result.values()):
        raise TypeError(f"{name} values must be integers")
    return result


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-blank text")
    return value


def _require_keys(payload: Mapping[str, Any], expected: set[str], name: str) -> None:
    missing = expected - set(payload)
    unknown = set(payload) - expected
    if missing or unknown:
        raise ValueError(
            f"{name} keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
