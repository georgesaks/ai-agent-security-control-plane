"""Security gateway for MCP tool requests.

The gateway is the enforcement point. It receives identity and environment
context, asks the policy layer for a decision, records audit evidence, and
only then dispatches to an approved MCP tool implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from policy.engine import PolicyContext, evaluate
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


def dispatch_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: MCPRequestContext,
    tool_registry: Dict[str, ToolHandler],
) -> GatewayResult:
    """Authorize and dispatch an MCP tool request using default-deny behavior."""
    if tool_name not in tool_registry:
        reason = "requested MCP tool is not registered with the security gateway"
        event = build_audit_event(
            actor=context.actor,
            role=context.role,
            environment=context.environment,
            tool_name=tool_name,
            decision="DENY",
            reason=reason,
        )
        return GatewayResult(False, reason, event.to_json())

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
