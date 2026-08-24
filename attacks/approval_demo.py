"""Demonstrate human approval gating a sensitive AI-agent action."""

from approval.workflow import clear_approvals, review_approval
from mcp_server.gateway import MCPRequestContext, dispatch_tool
from mcp_server.server import TOOL_REGISTRY
from response.containment import clear_containment
from risk.adaptive_risk import reset_risk


ACTOR = "llm-agent-approval-lab"
ARGUMENTS = {"title": "Approved security task", "body": "Human-reviewed agent draft"}


def request_id_from(result: str) -> str:
    return result.split("request_id=", 1)[1]


def main() -> None:
    clear_approvals()
    clear_containment(ACTOR)
    reset_risk(ACTOR)

    context = MCPRequestContext(ACTOR, "developer", "development")
    first = dispatch_tool("create_issue_draft", ARGUMENTS, context, TOOL_REGISTRY)
    print("SENSITIVE ACTION: development create_issue_draft")
    print(f"GATEWAY: {first.output}")
    print(f"AUDIT: {first.audit_json}")

    request_id = request_id_from(first.output)
    reviewed = review_approval(request_id, reviewer="security-reviewer-saki", approve=True)
    print(f"HUMAN REVIEW: {reviewed.status} | reviewer={reviewed.reviewed_by}")

    approved_context = MCPRequestContext(ACTOR, "developer", "development", approval_id=request_id)
    second = dispatch_tool("create_issue_draft", ARGUMENTS, approved_context, TOOL_REGISTRY)
    print(f"POST-APPROVAL RESULT: {'ALLOW' if second.allowed else 'DENY'}")
    print(f"OUTPUT: {second.output}")
    print(f"AUDIT: {second.audit_json}")

    replay = dispatch_tool("create_issue_draft", ARGUMENTS, approved_context, TOOL_REGISTRY)
    print("APPROVAL REPLAY TEST:")
    print(f"RESULT: {'ALLOW' if replay.allowed else 'DENY'}")
    print(f"DETAIL: {replay.output}")


if __name__ == "__main__":
    main()
