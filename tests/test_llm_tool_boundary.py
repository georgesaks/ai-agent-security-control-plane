"""Tests proving model-selected tools still cross the security boundary."""

import os
import unittest
from unittest.mock import patch

from identity.agent_identity import issue_token
from llm_agent.agent import execute_model_tool


TEST_SECRET = "llm-boundary-test-secret"


class LLMToolBoundaryTests(unittest.TestCase):
    def _token(self, role: str = "developer") -> str:
        return issue_token(
            actor="llm-agent-test",
            role=role,
            signing_secret=TEST_SECRET,
        )

    @patch.dict(os.environ, {"AGENT_IDENTITY_SIGNING_SECRET": TEST_SECRET})
    def test_model_selected_read_can_execute(self) -> None:
        result = execute_model_tool(
            tool_name="read_repository_summary",
            arguments={},
            identity_token=self._token(),
            environment="development",
        )

        self.assertTrue(result.startswith("ALLOWED:"))

    @patch.dict(os.environ, {"AGENT_IDENTITY_SIGNING_SECRET": TEST_SECRET})
    def test_model_selected_production_write_is_denied(self) -> None:
        result = execute_model_tool(
            tool_name="create_issue_draft",
            arguments={"title": "prod", "body": "attempt"},
            identity_token=self._token(),
            environment="production",
        )

        self.assertTrue(result.startswith("DENIED:"))
        self.assertIn("production", result)

    @patch.dict(os.environ, {"AGENT_IDENTITY_SIGNING_SECRET": TEST_SECRET})
    def test_unexpected_model_tool_is_default_denied(self) -> None:
        result = execute_model_tool(
            tool_name="read_secrets",
            arguments={},
            identity_token=self._token(),
            environment="development",
        )

        self.assertTrue(result.startswith("DENIED:"))
        self.assertIn("not registered", result)

    @patch.dict(os.environ, {"AGENT_IDENTITY_SIGNING_SECRET": TEST_SECRET})
    def test_verified_auditor_cannot_write_even_if_model_selects_write(self) -> None:
        result = execute_model_tool(
            tool_name="create_issue_draft",
            arguments={"title": "escalate", "body": "attempt"},
            identity_token=self._token(role="auditor"),
            environment="development",
        )

        self.assertTrue(result.startswith("DENIED:"))
        self.assertIn("auditor", result)


if __name__ == "__main__":
    unittest.main()
