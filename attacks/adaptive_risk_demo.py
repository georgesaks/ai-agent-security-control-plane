"""Demonstrate progressive, risk-based authorization for an AI agent."""

from mcp_server.gateway import MCPRequestContext, dispatch_tool
from mcp_server.server import TOOL_REGISTRY
from response.containment import clear_containment
from risk.adaptive_risk import get_risk, reset_risk, risk_for_denied_production_write


ACTOR = "llm-agent-adaptive-risk-lab"


def show_state(label: str) -> None:
    risk = get_risk(ACTOR)
    print(f"{label}: score={risk.score} level={risk.level}")


def main() -> None:
    reset_risk(ACTOR)
    clear_containment(ACTOR)
    show_state("INITIAL RISK")

    production = MCPRequestContext(ACTOR, "developer", "production")

    for attempt in range(1, 4):
        result = dispatch_tool(
            tool_name="create_issue_draft",
            arguments={"title": "risk demo", "body": "simulated write"},
            context=production,
            tool_registry=TOOL_REGISTRY,
        )
        print(f"PRODUCTION WRITE {attempt}: {'ALLOW' if result.allowed else 'DENY'}")
        if not result.allowed:
            state = risk_for_denied_production_write(ACTOR)
            print(f"RISK UPDATE: +30 -> score={state.score} level={state.level}")

        if attempt == 2:
            # At score 60 the agent is HIGH risk. Demonstrate that a write in
            # development, normally allowed for this role, is now restricted.
            restricted = dispatch_tool(
                tool_name="create_issue_draft",
                arguments={"title": "dev write", "body": "should be risk-blocked"},
                context=MCPRequestContext(ACTOR, "developer", "development"),
                tool_registry=TOOL_REGISTRY,
            )
            print("HIGH-RISK ADAPTIVE TEST: development create_issue_draft")
            print(f"RESULT: {'ALLOW' if restricted.allowed else 'DENY'}")
            print(f"DETAIL: {restricted.output}")

    show_state("FINAL RISK")

    # Score 90 is CRITICAL. Even a normally allowed development read should
    # cause quarantine and be denied.
    final = dispatch_tool(
        tool_name="read_repository_summary",
        arguments={},
        context=MCPRequestContext(ACTOR, "developer", "development"),
        tool_registry=TOOL_REGISTRY,
    )
    print("CRITICAL-RISK TEST: development read_repository_summary")
    print(f"RESULT: {'ALLOW' if final.allowed else 'DENY'}")
    print(f"DETAIL: {final.output}")
    print(f"AUDIT: {final.audit_json}")


if __name__ == "__main__":
    main()
