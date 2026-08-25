"""OPA/Rego policy adapter for the AI-agent security control plane.

This adapter is deliberately fail closed. If OPA is unavailable, the policy
cannot be parsed, the decision is undefined, or the response shape is invalid,
the caller receives a DENY decision rather than falling back to allow.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from policy.engine import PolicyContext, PolicyDecision, UNKNOWN


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGO_POLICY = ROOT / "policy" / "opa" / "agent_policy.rego"


class OPAEvaluationError(RuntimeError):
    """Raised when OPA cannot produce a trustworthy authorization decision."""


def _deny_closed(reason: str) -> PolicyDecision:
    return PolicyDecision(False, reason, UNKNOWN)


def evaluate_opa(
    context: PolicyContext,
    *,
    opa_binary: str | None = None,
    policy_path: Path = DEFAULT_REGO_POLICY,
) -> PolicyDecision:
    """Evaluate authorization with OPA and return a normalized policy decision."""
    opa = opa_binary or shutil.which("opa")
    if not opa:
        return _deny_closed("OPA policy engine unavailable; denied by fail-closed policy")

    payload = {
        "actor": context.actor,
        "role": context.role,
        "environment": context.environment,
        "tool_name": context.tool_name,
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as handle:
        json.dump(payload, handle)
        input_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [
                opa,
                "eval",
                "--format=json",
                "--input",
                str(input_path),
                "--data",
                str(policy_path),
                "data.aiagent.authz.decision",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode != 0:
            return _deny_closed("OPA evaluation failed; denied by fail-closed policy")

        try:
            document = json.loads(completed.stdout)
            value = document["result"][0]["expressions"][0]["value"]
            allowed = value["allowed"]
            reason = value["reason"]
            classification = value["classification"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return _deny_closed("OPA returned an invalid decision; denied by fail-closed policy")

        if not isinstance(allowed, bool) or not isinstance(reason, str) or not isinstance(classification, str):
            return _deny_closed("OPA returned an invalid decision; denied by fail-closed policy")

        return PolicyDecision(allowed, reason, classification)
    except (OSError, subprocess.SubprocessError):
        return _deny_closed("OPA policy engine error; denied by fail-closed policy")
    finally:
        input_path.unlink(missing_ok=True)
