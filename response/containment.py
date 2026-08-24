"""In-memory containment state for AI agents.

This prototype keeps containment deliberately simple and explainable. A SOC or
policy workflow can quarantine an actor after high-confidence detection. The
security gateway can then deny subsequent tool access for that actor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ContainmentRecord:
    actor: str
    state: str
    reason: str
    timestamp: str


_QUARANTINED: dict[str, ContainmentRecord] = {}


def quarantine_actor(actor: str, *, reason: str) -> ContainmentRecord:
    record = ContainmentRecord(
        actor=actor,
        state="QUARANTINED",
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    _QUARANTINED[actor] = record
    return record


def is_quarantined(actor: str) -> bool:
    return actor in _QUARANTINED


def get_containment(actor: str) -> ContainmentRecord | None:
    return _QUARANTINED.get(actor)


def clear_containment(actor: str) -> None:
    _QUARANTINED.pop(actor, None)
