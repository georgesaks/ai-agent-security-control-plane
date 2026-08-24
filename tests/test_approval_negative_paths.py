"""Negative-path security tests for human approval authorization."""

import unittest

from approval.workflow import (
    clear_approvals,
    consume_approval,
    create_approval_request,
    review_approval,
)


class ApprovalNegativePathTests(unittest.TestCase):
    actor = "approval-negative-test-agent"
    role = "developer"
    environment = "development"
    tool = "create_issue_draft"
    arguments = {"title": "approved", "body": "reviewed"}

    def tearDown(self) -> None:
        clear_approvals()

    def test_nonexistent_approval_is_denied(self) -> None:
        allowed, reason = consume_approval(
            "apr_missing", actor=self.actor, role=self.role,
            environment=self.environment, tool_name=self.tool,
            arguments=self.arguments,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "approval request not found")

    def test_rejected_approval_is_denied(self) -> None:
        request = create_approval_request(
            actor=self.actor, role=self.role, environment=self.environment,
            tool_name=self.tool, arguments=self.arguments,
        )
        review_approval(request.request_id, reviewer="reviewer", approve=False)
        allowed, reason = consume_approval(
            request.request_id, actor=self.actor, role=self.role,
            environment=self.environment, tool_name=self.tool,
            arguments=self.arguments,
        )
        self.assertFalse(allowed)
        self.assertIn("rejected", reason)

    def test_modified_arguments_cannot_use_approved_request(self) -> None:
        request = create_approval_request(
            actor=self.actor, role=self.role, environment=self.environment,
            tool_name=self.tool, arguments=self.arguments,
        )
        review_approval(request.request_id, reviewer="reviewer", approve=True)
        allowed, reason = consume_approval(
            request.request_id, actor=self.actor, role=self.role,
            environment=self.environment, tool_name=self.tool,
            arguments={"title": "approved", "body": "tampered"},
        )
        self.assertFalse(allowed)
        self.assertIn("does not match", reason)

    def test_approval_cannot_be_replayed(self) -> None:
        request = create_approval_request(
            actor=self.actor, role=self.role, environment=self.environment,
            tool_name=self.tool, arguments=self.arguments,
        )
        review_approval(request.request_id, reviewer="reviewer", approve=True)
        first, _ = consume_approval(
            request.request_id, actor=self.actor, role=self.role,
            environment=self.environment, tool_name=self.tool,
            arguments=self.arguments,
        )
        second, reason = consume_approval(
            request.request_id, actor=self.actor, role=self.role,
            environment=self.environment, tool_name=self.tool,
            arguments=self.arguments,
        )
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertIn("consumed", reason)


if __name__ == "__main__":
    unittest.main()
