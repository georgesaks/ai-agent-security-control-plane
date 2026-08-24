"""Client for asking Open Policy Agent for an authorization decision."""

from __future__ import annotations

from dataclasses import dataclass
import json
from urllib import error, request

from policy.engine import PolicyContext, PolicyDecision


@dataclass(frozen=True)
class OPAConfig:
    url: str = "http://localhost:8181/v1/data/agent/authz"
    timeout_seconds: float = 2.0


def evaluate_with_opa(
    context: PolicyContext,
    config: OPAConfig = OPAConfig(),
) -> PolicyDecision:
    """Send security context to OPA and fail closed if no decision is available."""
    payload = json.dumps(
        {
            "input": {
                "actor": context.actor,
                "role": context.role,
                "environment": context.environment,
                "tool_name": context.tool_name,
            }
        }
    ).encode("utf-8")

    req = request.Request(
        config.url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return PolicyDecision(
            allowed=False,
            reason=f"OPA decision unavailable; failing closed ({type(exc).__name__})",
        )

    result = body.get("result")
    if not isinstance(result, dict):
        return PolicyDecision(
            allowed=False,
            reason="OPA returned no valid decision; failing closed",
        )

    allowed = result.get("allow") is True
    reason = result.get("reason", "OPA policy denied the request")

    return PolicyDecision(allowed=allowed, reason=reason)
