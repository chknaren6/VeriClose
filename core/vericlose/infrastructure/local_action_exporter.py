"""Filesystem adapter for approved journal CSV and evidence-backed action records."""

from __future__ import annotations

import csv
import io
from hashlib import sha256
from pathlib import Path

from core.vericlose.domain.actions import ProposedAction
from core.vericlose.domain.enums import ActionType
from core.vericlose.ports.action_exporter import ExportedArtifact


class LocalActionExporter:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def export(self, run_id: str, action: ProposedAction) -> ExportedArtifact:
        if action.action_type is ActionType.JOURNAL_EXPORT:
            content = self._journal_csv(action)
            extension = ".csv"
            media_type = "text/csv"
        else:
            content = self._action_markdown(action)
            extension = ".md"
            media_type = "text/markdown"
        digest = sha256(content).hexdigest()
        relative = (
            Path("runs") / run_id / "exports" / f"{action.action_id}-{digest[:12]}{extension}"
        )
        target = (self._root / relative).resolve()
        if not target.is_relative_to(self._root):
            raise ValueError("export path escapes the configured data directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as handle:
                handle.write(content)
        except FileExistsError:
            if target.read_bytes() != content:
                raise ValueError("immutable export path contains different bytes") from None
        return ExportedArtifact(relative.as_posix(), media_type, digest, len(content))

    def read(self, artifact: ExportedArtifact) -> bytes:
        target = (self._root / artifact.relative_path).resolve()
        if not target.is_relative_to(self._root):
            raise ValueError("artifact path escapes the configured data directory")
        content = target.read_bytes()
        if sha256(content).hexdigest() != artifact.sha256:
            raise ValueError("exported artifact failed its integrity check")
        return content

    @staticmethod
    def _journal_csv(action: ProposedAction) -> bytes:
        if action.journal is None:
            raise ValueError("journal action has no journal proposal")
        payload = dict(action.payload)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=(
                "action_id",
                "case_id",
                "line_number",
                "account_code",
                "direction",
                "amount_minor",
                "currency",
                "reference",
                "narration",
                "policy_version",
                "evidence_ids",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        for number, line in enumerate(action.journal.lines, start=1):
            writer.writerow(
                {
                    "action_id": action.action_id,
                    "case_id": action.case_id,
                    "line_number": number,
                    "account_code": line.account_code,
                    "direction": line.direction.value,
                    "amount_minor": line.money.amount_minor,
                    "currency": line.money.currency,
                    "reference": payload.get("reference", ""),
                    "narration": line.narration,
                    "policy_version": payload.get("policy_version", ""),
                    "evidence_ids": "|".join(
                        link.event_id for link in line.evidence_links if link.event_id
                    ),
                }
            )
        return output.getvalue().encode("utf-8")

    @staticmethod
    def _action_markdown(action: ProposedAction) -> bytes:
        payload = dict(action.payload)
        evidence = ", ".join(link.event_id for link in action.evidence_links if link.event_id)
        clarification = payload.get(
            "clarification_text", payload.get("rationale", "Please review the cited evidence.")
        )
        heading = (
            "Evidence clarification request"
            if action.action_type is ActionType.CLARIFICATION_REQUEST
            else "Approved VeriClose action record"
        )
        body = (
            f"# {heading}\n\n"
            f"Action: `{action.action_type.value}`\n\n"
            f"Case: `{action.case_id}`\n\n"
            f"Reference: `{payload.get('reference', 'not available')}`\n\n"
            f"{clarification}\n\n"
            f"Cited evidence IDs: {evidence or 'none'}\n\n"
            "This artifact records an approved proposal only. It does not mutate source data, "
            "post to an ERP, or change deterministic proof.\n"
        )
        return body.encode("utf-8")
