"""Append-only operational audit events."""

from dataclasses import dataclass
from datetime import datetime

from core.vericlose.domain.events import _require_text


@dataclass(frozen=True, slots=True)
class AuditEvent:
    audit_id: str
    run_id: str
    event_type: str
    occurred_at: datetime
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.audit_id, "audit_id")
        _require_text(self.run_id, "run_id")
        _require_text(self.event_type, "event_type")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        if not isinstance(self.details, tuple) or any(
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not all(isinstance(value, str) for value in pair)
            for pair in self.details
        ):
            raise TypeError("details must be an immutable tuple of string pairs")
