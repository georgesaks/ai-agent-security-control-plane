"""Tests for adaptive AI-agent risk scoring and enforcement."""

import unittest

from mcp_server.gateway import MCPRequestContext, dispatch_tool
from response.containment import clear_containment, is_quarantined
from risk.adaptive_risk import add_risk, get_risk, reset_risk


class AdaptiveRiskTests(unittest.TestCase):
    actor = "adaptive-risk-test-agent"

    def tearDown(self) -> None:
        reset_risk(self.actor)
        clear_containment(self.actor)

    def test_risk_levels_progress_with_score(self) -> None:
        self.assertEqual(get_risk(self.actor).level, "LOW")
        self.assertEqual(add_risk(self.actor, 30).level, "MEDIUM")
        self.assertEqual(add_risk(self.actor, 30).level, "HIGH")
        self.assertEqual(add_risk(self.actor, 20).level, "CRITICAL")

    def test_high_risk_blocks_normally_allowed_development_write(self) -> None:
        add_risk(self.actor, 60)
        called = {"value": False}

        def write_tool(**kwargs) -> str:
            called["value"] = True
            return "executed"

        result = dispatch_tool(
            "create_issue_draft",
            {"title": "x", "body": "y"},
            MCPRequestContext(self.actor, "developer", "development"),
            {"create_issue_draft": write_tool},
        )
        self.assertFalse(result.allowed)
        self.assertIn("adaptive risk HIGH", result.output)
        self.assertFalse(called["value"])

    def test_critical_risk_quarantines_and_blocks_read(self) -> None:
        add_risk(self.actor, 80)
        result = dispatch_tool(
            "read_repository_summary",
            {},
            MCPRequestContext(self.actor, "developer", "development"),
            {"read_repository_summary": lambda: "approved"},
        )
        self.assertFalse(result.allowed)
        self.assertTrue(is_quarantined(self.actor))
        self.assertIn("CRITICAL", result.output)


if __name__ == "__main__":
    unittest.main()
