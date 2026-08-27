"""Evaluation-only labels. Runtime packages must never import this module."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from core.vericlose.domain.enums import (
    ActionType,
    ExceptionCategory,
    ProofLevel,
    Severity,
    SourceType,
)


def source_key(source_type: SourceType, source_record_id: str) -> str:
    """Namespace source IDs so equal IDs from different systems cannot collide."""

    return f"{source_type.value}:{source_record_id}"


@dataclass(frozen=True, slots=True)
class EventTruth:
    source_type: SourceType
    source_record_id: str
    expected_case_id: str
    expected_role: str

    @property
    def key(self) -> str:
        return source_key(self.source_type, self.source_record_id)

    def to_dict(self) -> dict[str, str]:
        return {
            "source_type": self.source_type.value,
            "source_record_id": self.source_record_id,
            "expected_case_id": self.expected_case_id,
            "expected_role": self.expected_role,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EventTruth:
        return cls(
            source_type=SourceType(payload["source_type"]),
            source_record_id=str(payload["source_record_id"]),
            expected_case_id=str(payload["expected_case_id"]),
            expected_role=str(payload["expected_role"]),
        )


@dataclass(frozen=True, slots=True)
class CaseTruth:
    case_id: str
    scenario: str
    expected_member_keys: tuple[str, ...]
    expected_proof_level: ProofLevel
    expected_exception_category: ExceptionCategory | None
    expected_severity: Severity | None
    expected_next_action: ActionType
    valid_timing_difference: bool
    description: str

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.scenario.strip():
            raise ValueError("case_id and scenario cannot be blank")
        if not self.expected_member_keys:
            raise ValueError("a truth case must contain at least one source member")
        if len(set(self.expected_member_keys)) != len(self.expected_member_keys):
            raise ValueError("truth member keys must be unique")
        if self.expected_proof_level is ProofLevel.PROVED:
            if self.expected_exception_category is not None or self.expected_severity is not None:
                raise ValueError("PROVED truth cannot carry exception classification")
        elif self.expected_exception_category is None or self.expected_severity is None:
            raise ValueError("non-PROVED truth requires exception category and severity")

    def with_outcome(
        self,
        *,
        scenario: str,
        proof_level: ProofLevel,
        category: ExceptionCategory | None,
        severity: Severity | None,
        next_action: ActionType,
        valid_timing_difference: bool = False,
        description: str,
        member_keys: tuple[str, ...] | None = None,
    ) -> CaseTruth:
        return replace(
            self,
            scenario=scenario,
            expected_proof_level=proof_level,
            expected_exception_category=category,
            expected_severity=severity,
            expected_next_action=next_action,
            valid_timing_difference=valid_timing_difference,
            description=description,
            expected_member_keys=member_keys or self.expected_member_keys,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "scenario": self.scenario,
            "expected_member_keys": list(self.expected_member_keys),
            "expected_proof_level": self.expected_proof_level.value,
            "expected_exception_category": (
                self.expected_exception_category.value
                if self.expected_exception_category is not None
                else None
            ),
            "expected_severity": (
                self.expected_severity.value if self.expected_severity is not None else None
            ),
            "expected_next_action": self.expected_next_action.value,
            "valid_timing_difference": self.valid_timing_difference,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CaseTruth:
        category = payload.get("expected_exception_category")
        severity = payload.get("expected_severity")
        valid_timing_difference = payload["valid_timing_difference"]
        if not isinstance(valid_timing_difference, bool):
            raise TypeError("valid_timing_difference must be a boolean")
        return cls(
            case_id=str(payload["case_id"]),
            scenario=str(payload["scenario"]),
            expected_member_keys=tuple(str(value) for value in payload["expected_member_keys"]),
            expected_proof_level=ProofLevel(payload["expected_proof_level"]),
            expected_exception_category=ExceptionCategory(category) if category else None,
            expected_severity=Severity(severity) if severity else None,
            expected_next_action=ActionType(payload["expected_next_action"]),
            valid_timing_difference=valid_timing_difference,
            description=str(payload["description"]),
        )


@dataclass(frozen=True, slots=True)
class TruthDataset:
    schema_version: str
    seed: int
    event_labels: tuple[EventTruth, ...]
    case_labels: tuple[CaseTruth, ...]

    def __post_init__(self) -> None:
        event_keys = [label.key for label in self.event_labels]
        case_ids = [label.case_id for label in self.case_labels]
        if len(set(event_keys)) != len(event_keys):
            raise ValueError("event truth keys must be unique")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("truth case IDs must be unique")

    def case(self, case_id: str) -> CaseTruth:
        try:
            return next(case for case in self.case_labels if case.case_id == case_id)
        except StopIteration as error:
            raise KeyError(case_id) from error

    def replace_case(self, updated: CaseTruth) -> TruthDataset:
        if updated.case_id not in {case.case_id for case in self.case_labels}:
            raise KeyError(updated.case_id)
        return replace(
            self,
            case_labels=tuple(
                updated if case.case_id == updated.case_id else case
                for case in self.case_labels
            ),
        )

    def replace_case_events(
        self,
        case_id: str,
        event_labels: tuple[EventTruth, ...],
    ) -> TruthDataset:
        retained = tuple(
            label for label in self.event_labels if label.expected_case_id != case_id
        )
        return replace(self, event_labels=retained + event_labels)

    def add_case(self, case: CaseTruth, events: tuple[EventTruth, ...]) -> TruthDataset:
        return replace(
            self,
            event_labels=self.event_labels + events,
            case_labels=self.case_labels + (case,),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "seed": self.seed,
            "event_labels": [label.to_dict() for label in self.event_labels],
            "case_labels": [label.to_dict() for label in self.case_labels],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TruthDataset:
        seed = payload["seed"]
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError("truth seed must be an integer")
        return cls(
            schema_version=str(payload["schema_version"]),
            seed=seed,
            event_labels=tuple(EventTruth.from_dict(item) for item in payload["event_labels"]),
            case_labels=tuple(CaseTruth.from_dict(item) for item in payload["case_labels"]),
        )
