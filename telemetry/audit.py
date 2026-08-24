"""Structured audit telemetry for agent authorization decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    actor: str
    role: str
    environment: str
    tool_name: str
    decision: str
    reason: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def build_audit_event(
    *,
    actor: str,
    role: str,
    environment: str,
    tool_name: str,
    decision: str,
    reason: str,
) -> AuditEvent:
    return AuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
        decision=decision,
        reason=reason,
    )
