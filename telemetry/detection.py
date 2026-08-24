"""Detection rules for AI agent authorization telemetry.

The rules are intentionally simple and explainable. They operate on the same
structured audit events produced by the MCP security gateway and demonstrate
how agent activity can feed a SOC/SIEM detection pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from telemetry.audit import AuditEvent


@dataclass(frozen=True)
class Detection:
    rule_id: str
    severity: str
    title: str
    actor: str
    tool_name: str
    reason: str


def detect_event(event: AuditEvent) -> list[Detection]:
    findings: list[Detection] = []

    if event.decision == "DENY" and event.environment == "production":
        findings.append(
            Detection(
                rule_id="AI-001",
                severity="HIGH",
                title="Denied AI agent action in production",
                actor=event.actor,
                tool_name=event.tool_name,
                reason=event.reason,
            )
        )

    if event.decision == "DENY" and event.tool_name == "create_issue_draft":
        findings.append(
            Detection(
                rule_id="AI-002",
                severity="HIGH",
                title="Blocked write-oriented agent action",
                actor=event.actor,
                tool_name=event.tool_name,
                reason=event.reason,
            )
        )

    return findings


def detect_repeated_denials(
    events: Iterable[AuditEvent], *, threshold: int = 3
) -> list[Detection]:
    counts: dict[str, int] = {}
    last_event: dict[str, AuditEvent] = {}

    for event in events:
        if event.decision != "DENY":
            continue
        counts[event.actor] = counts.get(event.actor, 0) + 1
        last_event[event.actor] = event

    findings: list[Detection] = []
    for actor, count in counts.items():
        if count >= threshold:
            event = last_event[actor]
            findings.append(
                Detection(
                    rule_id="AI-003",
                    severity="CRITICAL",
                    title="Repeated denied actions by AI agent",
                    actor=actor,
                    tool_name=event.tool_name,
                    reason=f"{count} denied actions observed; threshold={threshold}",
                )
            )

    return findings
