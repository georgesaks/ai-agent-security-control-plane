"""Authorization and action-classification policy for the agent prototype.

Policy answers two separate questions: whether the caller is allowed to request
a tool at all, and how sensitive that tool is. The gateway consumes the
classification to select the required enforcement workflow. Keeping this logic
centralized prepares the project for a later external policy engine such as
OPA/Rego.
"""

from dataclasses import dataclass


READ_ONLY = "READ_ONLY"
SENSITIVE = "SENSITIVE"
CRITICAL = "CRITICAL"
UNKNOWN = "UNKNOWN"


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
    action_classification: str = UNKNOWN


ROLE_PERMISSIONS = {
    "developer": {
        "read_repository_summary",
        "create_issue_draft",
        "critical_configuration_change",
    },
    "auditor": {
        "read_repository_summary",
    },
}


ACTION_CLASSIFICATIONS = {
    "read_repository_summary": READ_ONLY,
    "create_issue_draft": SENSITIVE,
    "critical_configuration_change": CRITICAL,
}


def classify_action(tool_name: str) -> str:
    """Return the policy sensitivity class for a registered tool name."""
    return ACTION_CLASSIFICATIONS.get(tool_name, UNKNOWN)


def evaluate(context: PolicyContext) -> PolicyDecision:
    """Evaluate role/environment authorization and return action sensitivity."""
    classification = classify_action(context.tool_name)
    allowed_tools = ROLE_PERMISSIONS.get(context.role, set())

    if context.tool_name not in allowed_tools:
        return PolicyDecision(
            allowed=False,
            reason=f"role '{context.role}' is not allowed to use '{context.tool_name}'",
            action_classification=classification,
        )

    if classification == UNKNOWN:
        return PolicyDecision(
            allowed=False,
            reason="tool has no security classification and is denied by default",
            action_classification=UNKNOWN,
        )

    if context.environment == "production" and classification in {SENSITIVE, CRITICAL}:
        return PolicyDecision(
            allowed=False,
            reason="write-oriented actions are blocked in production in this prototype",
            action_classification=classification,
        )

    return PolicyDecision(
        allowed=True,
        reason="policy requirements satisfied",
        action_classification=classification,
    )
