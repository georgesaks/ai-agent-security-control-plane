"""Tests for the first constrained agent prototype."""

import unittest

from agent.main import run_tool


class AgentToolAccessTests(unittest.TestCase):
    def test_approved_tool_is_allowed(self) -> None:
        result = run_tool("read_repository_summary")

        self.assertTrue(result.startswith("ALLOWED:"))
        self.assertIn("read_repository_summary", result)

    def test_second_approved_tool_is_allowed(self) -> None:
        result = run_tool("create_issue_draft")

        self.assertTrue(result.startswith("ALLOWED:"))
        self.assertIn("No GitHub write was performed", result)

    def test_unapproved_tool_is_denied(self) -> None:
        result = run_tool("delete_repository")

        self.assertTrue(result.startswith("DENIED:"))
        self.assertIn("not available", result)

    def test_unknown_tool_is_denied_by_default(self) -> None:
        result = run_tool("read_production_secrets")

        self.assertTrue(result.startswith("DENIED:"))


if __name__ == "__main__":
    unittest.main()
