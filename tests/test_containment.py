"""Tests for AI agent containment and gateway enforcement."""

import unittest

from mcp_server.gateway import MCPRequestContext, dispatch_tool
from response.containment import clear_containment, is_quarantined, quarantine_actor


class ContainmentTests(unittest.TestCase):
    actor = "containment-test-agent"

    def tearDown(self) -> None:
        clear_containment(self.actor)

    def test_actor_can_be_quarantined(self) -> None:
        quarantine_actor(self.actor, reason="critical detection")
        self.assertTrue(is_quarantined(self.actor))

    def test_quarantined_actor_is_denied_normally_allowed_read(self) -> None:
        quarantine_actor(self.actor, reason="AI-003 repeated denials")
        called = {"value": False}

        def approved_read() -> str:
            called["value"] = True
            return "should not execute"

        result = dispatch_tool(
            tool_name="read_repository_summary",
            arguments={},
            context=MCPRequestContext(
                actor=self.actor,
                role="developer",
                environment="development",
            ),
            tool_registry={"read_repository_summary": approved_read},
        )

        self.assertFalse(result.allowed)
        self.assertIn("quarantined", result.output)
        self.assertFalse(called["value"])
        self.assertIn('"decision": "DENY"', result.audit_json)

    def test_cleared_quarantine_restores_policy_evaluation(self) -> None:
        quarantine_actor(self.actor, reason="temporary containment")
        clear_containment(self.actor)

        result = dispatch_tool(
            tool_name="read_repository_summary",
            arguments={},
            context=MCPRequestContext(
                actor=self.actor,
                role="developer",
                environment="development",
            ),
            tool_registry={"read_repository_summary": lambda: "approved"},
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.output, "approved")


if __name__ == "__main__":
    unittest.main()
