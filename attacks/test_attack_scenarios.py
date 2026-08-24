"""Safe attack simulations for the Phase 2 security lab.

These tests exercise identity and authorization failures without touching any
real cloud, GitHub, secret, or production resource.
"""

import unittest

from identity.agent_identity import IdentityError, issue_token, verify_token
from mcp_server.gateway import MCPRequestContext, dispatch_tool


TEST_SECRET = "attack-lab-signing-secret"


def read_tool() -> str:
    return "read executed"


def draft_tool(title: str, body: str) -> str:
    return f"draft executed: {title} ({len(body)})"


TOOL_REGISTRY = {
    "read_repository_summary": read_tool,
    "create_issue_draft": draft_tool,
}


class AttackSimulationTests(unittest.TestCase):
    def test_identity_spoofing_is_blocked(self) -> None:
        attacker_token = issue_token(
            actor="agent-attacker",
            role="auditor",
            signing_secret=TEST_SECRET,
        )
        payload, signature = attacker_token.split(".", 1)
        tampered_token = f"{payload[:-1]}A.{signature}"

        with self.assertRaises(IdentityError):
            verify_token(tampered_token, signing_secret=TEST_SECRET)

    def test_privilege_escalation_claim_cannot_be_self_asserted(self) -> None:
        token = issue_token(
            actor="agent-007",
            role="auditor",
            signing_secret=TEST_SECRET,
        )
        identity = verify_token(token, signing_secret=TEST_SECRET)

        result = dispatch_tool(
            "create_issue_draft",
            {"title": "escalation", "body": "attempt"},
            MCPRequestContext(identity.actor, identity.role, "development"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("auditor", result.output)

    def test_unregistered_tool_request_is_blocked(self) -> None:
        token = issue_token(
            actor="agent-008",
            role="developer",
            signing_secret=TEST_SECRET,
        )
        identity = verify_token(token, signing_secret=TEST_SECRET)

        result = dispatch_tool(
            "read_secrets",
            {},
            MCPRequestContext(identity.actor, identity.role, "development"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("not registered", result.output)

    def test_production_write_attempt_is_blocked(self) -> None:
        token = issue_token(
            actor="agent-009",
            role="developer",
            signing_secret=TEST_SECRET,
        )
        identity = verify_token(token, signing_secret=TEST_SECRET)

        result = dispatch_tool(
            "create_issue_draft",
            {"title": "prod write", "body": "should be denied"},
            MCPRequestContext(identity.actor, identity.role, "production"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("production", result.output)


if __name__ == "__main__":
    unittest.main()
