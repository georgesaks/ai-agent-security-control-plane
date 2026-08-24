"""Security gateway for MCP tool requests.

The gateway is the enforcement point. It receives identity and environment
context, checks containment and adaptive risk state, asks the policy layer for
a decision, records audit evidence, and only then dispatches an approved tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from policy.engine import PolicyContext, evaluate
from response.containment import get_containment, is_quarantined, quarantine_actor
from risk.adaptive_risk import get_risk
from telemetry.audit import build_audit_event


@dataclass(frozen=True)
class MCPRequestContext:
    actor: str
    role: str
    environment: str


@dataclass(frozen=True)
class GatewayResult:
    allowed: bool
    output: str
    audit_json: str


ToolHandler = Callable[..., str]


def _deny(tool_name: str, context: MCPRequestContext, reason: str) -> GatewayResult:
    event = build_audit_event(
        actor=context.actor,
        role=context.role,
        environment=context.environment,
        tool_name=tool_name,
        decision="DENY",
        reason=reason,
    )
    return GatewayResult(False, reason, event.to_json())


def dispatch_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: MCPRequestContext,
    tool_registry: Dict[str, ToolHandler],
) -> GatewayResult:
    """Authorize and dispatch an MCP tool request using default-deny behavior."""
    if is_quarantined(context.actor):
        containment = get_containment(context.actor)
        reason = (
            "agent is quarantined; all tool access is blocked"
            if containment is None
            else f"agent is quarantined: {containment.reason}"
        )
        return _deny(tool_name, context, reason)

    risk = get_risk(context.actor)
    if risk.level == "CRITICAL":
        quarantine_actor(
            context.actor,
            reason=f"adaptive risk score {risk.score} reached CRITICAL",
        )
        return _deny(
            tool_name,
            context,
            f"adaptive risk CRITICAL ({risk.score}); agent quarantined",
        )

    if risk.level == "HIGH" and tool_name == "create_issue_draft":
        return _deny(
            tool_name,
            context,
            f"adaptive risk HIGH ({risk.score}); write-oriented tool access restricted",
        )

    if tool_name not in tool_registry:
        return _deny(
            tool_name,
            context,
            "requested MCP tool is not registered with the security gateway",
        )

    policy_context = PolicyContext(
        actor=context.actor,
        role=context.role,
        environment=context.environment,
        tool_name=tool_name,
    )
    decision = evaluate(policy_context)

    event = build_audit_event(
        actor=context.actor,
        role=context.role,
        environment=context.environment,
        tool_name=tool_name,
        decision="ALLOW" if decision.allowed else "DENY",
        reason=decision.reason,
    )

    if not decision.allowed:
        return GatewayResult(False, decision.reason, event.to_json())

    output = tool_registry[tool_name](**arguments)
    return GatewayResult(True, output, event.to_json())
