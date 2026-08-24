"""Security gateway for MCP tool requests.

The gateway is the enforcement point. It checks containment, adaptive risk,
human approval requirements, and authorization policy before tool execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from approval.workflow import consume_approval, create_approval_request
from policy.engine import PolicyContext, evaluate
from response.containment import get_containment, is_quarantined, quarantine_actor
from risk.adaptive_risk import get_risk
from telemetry.audit import build_audit_event


@dataclass(frozen=True)
class MCPRequestContext:
    actor: str
    role: str
    environment: str
    approval_id: str | None = None


@dataclass(frozen=True)
class GatewayResult:
    allowed: bool
    output: str
    audit_json: str


ToolHandler = Callable[..., str]


def _result(tool_name: str, context: MCPRequestContext, decision: str, reason: str,
            *, allowed: bool = False) -> GatewayResult:
    event = build_audit_event(
        actor=context.actor,
        role=context.role,
        environment=context.environment,
        tool_name=tool_name,
        decision=decision,
        reason=reason,
    )
    return GatewayResult(allowed, reason, event.to_json())


def dispatch_tool(tool_name: str, arguments: Dict[str, Any], context: MCPRequestContext,
                  tool_registry: Dict[str, ToolHandler]) -> GatewayResult:
    if is_quarantined(context.actor):
        containment = get_containment(context.actor)
        reason = "agent is quarantined; all tool access is blocked" if containment is None else f"agent is quarantined: {containment.reason}"
        return _result(tool_name, context, "DENY", reason)

    risk = get_risk(context.actor)
    if risk.level == "CRITICAL":
        quarantine_actor(context.actor, reason=f"adaptive risk score {risk.score} reached CRITICAL")
        return _result(tool_name, context, "DENY", f"adaptive risk CRITICAL ({risk.score}); agent quarantined")

    if risk.level == "HIGH" and tool_name == "create_issue_draft":
        return _result(tool_name, context, "DENY", f"adaptive risk HIGH ({risk.score}); write-oriented tool access restricted")

    if tool_name not in tool_registry:
        return _result(tool_name, context, "DENY", "requested MCP tool is not registered with the security gateway")

    policy_context = PolicyContext(context.actor, context.role, context.environment, tool_name)
    decision = evaluate(policy_context)
    if not decision.allowed:
        return _result(tool_name, context, "DENY", decision.reason)

    # Development writes are permitted by role policy but are sensitive enough
    # to require explicit human authorization before execution.
    if context.environment == "development" and tool_name == "create_issue_draft":
        if context.approval_id is None:
            approval = create_approval_request(
                actor=context.actor,
                role=context.role,
                environment=context.environment,
                tool_name=tool_name,
                arguments=arguments,
            )
            return _result(tool_name, context, "REQUIRE_APPROVAL", f"human approval required; request_id={approval.request_id}")

        approved, reason = consume_approval(
            context.approval_id,
            actor=context.actor,
            role=context.role,
            environment=context.environment,
            tool_name=tool_name,
            arguments=arguments,
        )
        if not approved:
            return _result(tool_name, context, "DENY", reason)

        output = tool_registry[tool_name](**arguments)
        event = build_audit_event(
            actor=context.actor,
            role=context.role,
            environment=context.environment,
            tool_name=tool_name,
            decision="ALLOW",
            reason=f"policy requirements satisfied; human {reason}",
        )
        return GatewayResult(True, output, event.to_json())

    event = build_audit_event(
        actor=context.actor,
        role=context.role,
        environment=context.environment,
        tool_name=tool_name,
        decision="ALLOW",
        reason=decision.reason,
    )
    output = tool_registry[tool_name](**arguments)
    return GatewayResult(True, output, event.to_json())
