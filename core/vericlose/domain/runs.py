"""Immutable run manifest and legal reconciliation lifecycle transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from core.vericlose.domain.enums import RunState, SourceType
from core.vericlose.domain.events import _require_sha256, _require_text

VersionPairs = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class SourceFile:
    file_id: str
    source_type: SourceType
    sha256: str
    original_name: str
    size_bytes: int
    uploaded_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.file_id, "file_id")
        _require_text(self.original_name, "original_name")
        _require_sha256(self.sha256, "sha256")
        if not isinstance(self.source_type, SourceType):
            raise TypeError("source_type must be a SourceType")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise TypeError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")
        if self.uploaded_at.tzinfo is None or self.uploaded_at.utcoffset() is None:
            raise ValueError("uploaded_at must be timezone-aware")


ALLOWED_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.CREATED: frozenset({RunState.FILES_ATTACHED, RunState.CANCELLED}),
    RunState.FILES_ATTACHED: frozenset(
        {RunState.VALIDATED, RunState.FAILED_VALIDATION, RunState.CANCELLED}
    ),
    RunState.VALIDATED: frozenset({RunState.RECONCILING, RunState.CANCELLED}),
    RunState.RECONCILING: frozenset({RunState.COMPLETED, RunState.FAILED, RunState.CANCELLED}),
    RunState.COMPLETED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.FAILED_VALIDATION: frozenset(),
    RunState.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Reproducibility record for one import → verify → review run."""

    run_id: str
    state: RunState
    seed: int
    policy_version: str
    rule_version: str
    mapping_versions: VersionPairs
    input_files: tuple[SourceFile, ...]
    build_commit: str
    created_at: datetime

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.run_id, "run_id"),
            (self.policy_version, "policy_version"),
            (self.rule_version, "rule_version"),
            (self.build_commit, "build_commit"),
        ):
            _require_text(value, field_name)
        if not isinstance(self.state, RunState):
            raise TypeError("state must be a RunState")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise TypeError("seed must be an integer")
        if self.seed < 0:
            raise ValueError("seed cannot be negative")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if not isinstance(self.input_files, tuple):
            raise TypeError("input_files must be a tuple[SourceFile, ...]")
        if not isinstance(self.mapping_versions, tuple):
            raise TypeError("mapping_versions must be an immutable tuple of pairs")
        if any(
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not all(isinstance(value, str) and value.strip() for value in pair)
            for pair in self.mapping_versions
        ):
            raise ValueError("mapping_versions must contain non-blank (source, version) pairs")
        if len({source for source, _ in self.mapping_versions}) != len(self.mapping_versions):
            raise ValueError("mapping_versions source names must be unique")

    def transition(self, next_state: RunState) -> RunManifest:
        allowed = ALLOWED_TRANSITIONS[self.state]
        if next_state not in allowed:
            allowed_values = sorted(state.value for state in allowed)
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {next_state.value}; "
                f"allowed={allowed_values}"
            )
        return replace(self, state=next_state)

    def with_files(self, files: tuple[SourceFile, ...]) -> RunManifest:
        if self.state is not RunState.CREATED:
            raise ValueError("files can only be attached from CREATED")
        if not files:
            raise ValueError("at least one source file is required")
        if len({source_file.file_id for source_file in files}) != len(files):
            raise ValueError("source file IDs must be unique")
        return replace(self, input_files=files).transition(RunState.FILES_ATTACHED)
