"""Simple authorization layer for the agent prototype.

This version keeps policy decisions in Python so the security model is easy
to understand before moving to an external policy engine such as OPA.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyContext:
    actor: str
    role: str
    environment: str
    tool_name: str


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


ROLE_PERMISSIONS = {
    "developer": {
        "read_repository_summary",
        "create_issue_draft",
    },
    "auditor": {
        "read_repository_summary",
    },
}


def evaluate(context: PolicyContext) -> PolicyDecision:
    """Evaluate whether an actor may invoke a tool in the current context."""
    allowed_tools = ROLE_PERMISSIONS.get(context.role, set())

    if context.tool_name not in allowed_tools:
        return PolicyDecision(
            allowed=False,
            reason=f"role '{context.role}' is not allowed to use '{context.tool_name}'",
        )

    if context.environment == "production" and context.tool_name == "create_issue_draft":
        return PolicyDecision(
            allowed=False,
            reason="write-oriented actions are blocked in production in this prototype",
        )

    return PolicyDecision(
        allowed=True,
        reason="policy requirements satisfied",
    )
