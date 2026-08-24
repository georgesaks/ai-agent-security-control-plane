"""Tests for agent tool exposure and policy enforcement."""

import unittest

from agent.main import run_tool


class AgentToolAccessTests(unittest.TestCase):
    def test_developer_can_read_repository(self) -> None:
        result = run_tool("read_repository_summary")

        self.assertTrue(result.startswith("ALLOWED BY POLICY:"))
        self.assertIn("read_repository_summary", result)

    def test_developer_can_create_issue_draft_in_development(self) -> None:
        result = run_tool("create_issue_draft")

        self.assertTrue(result.startswith("ALLOWED BY POLICY:"))
        self.assertIn("No GitHub write was performed", result)

    def test_auditor_cannot_create_issue_draft(self) -> None:
        result = run_tool("create_issue_draft", role="auditor")

        self.assertTrue(result.startswith("DENIED BY POLICY:"))
        self.assertIn("auditor", result)

    def test_write_oriented_action_is_denied_in_production(self) -> None:
        result = run_tool("create_issue_draft", environment="production")

        self.assertTrue(result.startswith("DENIED BY POLICY:"))
        self.assertIn("production", result)

    def test_unexposed_tool_is_denied_before_policy(self) -> None:
        result = run_tool("delete_repository")

        self.assertTrue(result.startswith("DENIED:"))
        self.assertIn("not available", result)

    def test_unknown_role_has_no_permissions(self) -> None:
        result = run_tool("read_repository_summary", role="unknown-role")

        self.assertTrue(result.startswith("DENIED BY POLICY:"))


if __name__ == "__main__":
    unittest.main()
