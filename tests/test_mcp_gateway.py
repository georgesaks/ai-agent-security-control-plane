"""Tests for MCP authorization and dispatch behavior."""

import json
import unittest

from mcp_server.gateway import MCPRequestContext, dispatch_tool


def read_tool() -> str:
    return "read executed"


def draft_tool(title: str, body: str) -> str:
    return f"draft executed: {title} ({len(body)})"


TOOL_REGISTRY = {
    "read_repository_summary": read_tool,
    "create_issue_draft": draft_tool,
}


class MCPGatewayTests(unittest.TestCase):
    def test_developer_read_is_authorized_and_executed(self) -> None:
        result = dispatch_tool(
            "read_repository_summary",
            {},
            MCPRequestContext("agent-001", "developer", "development"),
            TOOL_REGISTRY,
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.output, "read executed")
        self.assertEqual(json.loads(result.audit_json)["decision"], "ALLOW")

    def test_auditor_write_is_denied_before_execution(self) -> None:
        result = dispatch_tool(
            "create_issue_draft",
            {"title": "test", "body": "should not execute"},
            MCPRequestContext("agent-002", "auditor", "development"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("auditor", result.output)
        self.assertEqual(json.loads(result.audit_json)["decision"], "DENY")

    def test_production_write_is_denied(self) -> None:
        result = dispatch_tool(
            "create_issue_draft",
            {"title": "test", "body": "blocked"},
            MCPRequestContext("agent-003", "developer", "production"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("production", result.output)

    def test_unregistered_mcp_tool_is_denied_by_default(self) -> None:
        result = dispatch_tool(
            "read_secrets",
            {},
            MCPRequestContext("agent-004", "developer", "development"),
            TOOL_REGISTRY,
        )

        self.assertFalse(result.allowed)
        self.assertIn("not registered", result.output)
        self.assertEqual(json.loads(result.audit_json)["decision"], "DENY")


if __name__ == "__main__":
    unittest.main()
