"""End-to-end detect, correlate, contain, and verify AI-agent quarantine."""

from __future__ import annotations

from mcp_server.gateway import MCPRequestContext, dispatch_tool
from mcp_server.server import TOOL_REGISTRY
from response.containment import clear_containment, quarantine_actor
from telemetry.audit import AuditEvent
from telemetry.detection import detect_repeated_denials

import json


ACTOR = "llm-agent-containment-lab"


def main() -> None:
    clear_containment(ACTOR)
    context = MCPRequestContext(
        actor=ACTOR,
        role="developer",
        environment="production",
    )

    events: list[AuditEvent] = []
    print(f"INITIAL STATE: TRUSTED | actor={ACTOR}")
    print()

    for attempt in range(1, 4):
        result = dispatch_tool(
            tool_name="create_issue_draft",
            arguments={
                "title": f"Unauthorized production write {attempt}",
                "body": "Simulated compromised-agent action",
            },
            context=context,
            tool_registry=TOOL_REGISTRY,
        )
        event = AuditEvent(**json.loads(result.audit_json))
        events.append(event)
        print(f"PRODUCTION WRITE {attempt}: {'ALLOW' if result.allowed else 'DENY'}")

    correlated = detect_repeated_denials(events)
    if not correlated:
        print("CONTAINMENT: not triggered")
        return

    finding = correlated[0]
    print(
        f"DETECTION: [{finding.severity}] {finding.rule_id} | "
        f"{finding.title}"
    )
    record = quarantine_actor(
        ACTOR,
        reason=f"{finding.rule_id}: {finding.reason}",
    )
    print(f"CONTAINMENT: actor state -> {record.state}")
    print(f"CONTAINMENT REASON: {record.reason}")
    print()

    # This read would normally be allowed for a developer. It must now be
    # blocked solely because the actor has entered quarantine.
    post_containment = dispatch_tool(
        tool_name="read_repository_summary",
        arguments={},
        context=MCPRequestContext(
            actor=ACTOR,
            role="developer",
            environment="development",
        ),
        tool_registry=TOOL_REGISTRY,
    )
    print("POST-CONTAINMENT TEST: read_repository_summary")
    print(f"RESULT: {'ALLOW' if post_containment.allowed else 'DENY'}")
    print(f"DETAIL: {post_containment.output}")
    print(f"AUDIT: {post_containment.audit_json}")


if __name__ == "__main__":
    main()
