"""Agent prototype with independent authorization and audit telemetry."""

from agent.tools import list_available_tools
from policy.engine import PolicyContext, evaluate
from telemetry.audit import build_audit_event


def run_tool(
    tool_name: str,
    *,
    actor: str = "local-user",
    role: str = "developer",
    environment: str = "development",
) -> str:
    tools = list_available_tools()

    if tool_name not in tools:
        event = build_audit_event(
            actor=actor,
            role=role,
            environment=environment,
            tool_name=tool_name,
            decision="DENY",
            reason="tool is not exposed to this agent",
        )
        return f"DENIED: tool '{tool_name}' is not available to this agent.\nAUDIT: {event.to_json()}"

    context = PolicyContext(
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
    )
    decision = evaluate(context)

    event = build_audit_event(
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
        decision="ALLOW" if decision.allowed else "DENY",
        reason=decision.reason,
    )

    if not decision.allowed:
        return f"DENIED BY POLICY: {decision.reason}\nAUDIT: {event.to_json()}"

    tool = tools[tool_name]
    return (
        f"ALLOWED BY POLICY: {tool.name}\n"
        f"ACTOR: {actor}\n"
        f"ROLE: {role}\n"
        f"ENVIRONMENT: {environment}\n"
        f"RESULT: {tool.handler()}\n"
        f"AUDIT: {event.to_json()}"
    )


def main() -> None:
    print("AI Agent Security Control Plane - Prototype 3")

    print("\nTest 1: developer reads repository in development")
    print(run_tool("read_repository_summary", actor="agent-001"))

    print("\nTest 2: auditor attempts issue draft")
    print(run_tool("create_issue_draft", actor="agent-002", role="auditor"))

    print("\nTest 3: developer attempts issue draft in production")
    print(
        run_tool(
            "create_issue_draft",
            actor="agent-003",
            environment="production",
        )
    )


if __name__ == "__main__":
    main()
