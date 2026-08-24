"""Generate security telemetry and detections for a compromised AI agent."""

from __future__ import annotations

import os

from identity.agent_identity import issue_token
from mcp_server.gateway import MCPRequestContext, dispatch_tool
from mcp_server.server import TOOL_REGISTRY
from telemetry.detection import detect_event, detect_repeated_denials


def main() -> None:
    signing_secret = os.environ.get("AGENT_IDENTITY_SIGNING_SECRET")
    if not signing_secret:
        print("DENIED: agent identity signing is not configured")
        return

    token = issue_token(
        actor="llm-agent-soc-lab",
        role="developer",
        signing_secret=signing_secret,
        ttl_seconds=300,
    )

    # Token issuance proves the actor has a signed identity. The gateway itself
    # consumes verified claims in the normal server path. Here we use the same
    # claims to generate a deterministic three-event detection demonstration.
    _ = token
    context = MCPRequestContext(
        actor="llm-agent-soc-lab",
        role="developer",
        environment="production",
    )

    events = []
    for attempt in range(1, 4):
        result = dispatch_tool(
            tool_name="create_issue_draft",
            arguments={
                "title": f"Production override attempt {attempt}",
                "body": "Simulated compromised-agent write attempt",
            },
            context=context,
            tool_registry=TOOL_REGISTRY,
        )
        print(f"ATTEMPT {attempt}: {'ALLOW' if result.allowed else 'DENY'}")
        print(f"AUDIT: {result.audit_json}")

        from telemetry.audit import AuditEvent
        import json

        events.append(AuditEvent(**json.loads(result.audit_json)))
        for finding in detect_event(events[-1]):
            print(
                f"ALERT: [{finding.severity}] {finding.rule_id} | "
                f"{finding.title} | actor={finding.actor} | tool={finding.tool_name}"
            )
        print()

    for finding in detect_repeated_denials(events):
        print(
            f"CORRELATED ALERT: [{finding.severity}] {finding.rule_id} | "
            f"{finding.title} | actor={finding.actor} | {finding.reason}"
        )


if __name__ == "__main__":
    main()
