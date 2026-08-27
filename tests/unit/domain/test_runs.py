from datetime import UTC, datetime

import pytest

from core.vericlose.domain.enums import RunState, SourceType
from core.vericlose.domain.runs import RunManifest, SourceFile


def _file(file_id: str = "file-1") -> SourceFile:
    return SourceFile(
        file_id=file_id,
        source_type=SourceType.GATEWAY,
        sha256="a" * 64,
        original_name="gateway.csv",
        size_bytes=100,
        uploaded_at=datetime(2026, 4, 1, tzinfo=UTC),
    )


def _manifest(**overrides: object) -> RunManifest:
    fields: dict[str, object] = {
        "run_id": "run-1",
        "state": RunState.CREATED,
        "seed": 42,
        "policy_version": "razorpay_inr_v1",
        "rule_version": "rules-v1",
        "mapping_versions": (("gateway", "v1"), ("bank", "v1")),
        "input_files": (),
        "build_commit": "abc123",
        "created_at": datetime(2026, 4, 1, tzinfo=UTC),
    }
    fields.update(overrides)
    return RunManifest(**fields)  # type: ignore[arg-type]


def test_happy_path_is_immutable() -> None:
    created = _manifest()
    completed = (
        created.with_files((_file(),))
        .transition(RunState.VALIDATED)
        .transition(RunState.RECONCILING)
        .transition(RunState.COMPLETED)
    )
    assert created.state is RunState.CREATED
    assert completed.state is RunState.COMPLETED


def test_invalid_transition_and_empty_files_fail() -> None:
    with pytest.raises(ValueError, match="Invalid transition"):
        _manifest().transition(RunState.COMPLETED)
    with pytest.raises(ValueError, match="at least one"):
        _manifest().with_files(())


def test_mapping_versions_are_immutable_pairs() -> None:
    with pytest.raises(TypeError, match="immutable tuple"):
        _manifest(mapping_versions={"gateway": "v1"})
