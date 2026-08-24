import unittest

from approval.workflow import clear_approvals, review_approval
from mcp_server.gateway import MCPRequestContext, dispatch_tool
from response.containment import clear_containment
from risk.adaptive_risk import reset_risk


class ApprovalTests(unittest.TestCase):
    actor = "approval-test-agent"
    reviewer = "security-reviewer-saki"

    def setUp(self):
        clear_approvals()
        clear_containment(self.actor)
        reset_risk(self.actor)

    def tearDown(self):
        clear_approvals()
        clear_containment(self.actor)
        reset_risk(self.actor)

    def _request(self, arguments):
        return dispatch_tool(
            "create_issue_draft", arguments,
            MCPRequestContext(self.actor, "developer", "development"),
            {"create_issue_draft": lambda **kwargs: "executed"},
        )

    def test_sensitive_action_requires_approval(self):
        result = self._request({"title": "x", "body": "y"})
        self.assertFalse(result.allowed)
        self.assertIn("sensitive action", result.output)
        self.assertIn("human approval", result.output)
        self.assertIn('"decision": "REQUIRE_APPROVAL"', result.audit_json)

    def test_approved_matching_action_executes_once(self):
        arguments = {"title": "x", "body": "y"}
        pending = self._request(arguments)
        request_id = pending.output.split("request_id=", 1)[1]
        review_approval(request_id, reviewer=self.reviewer, approve=True)
        context = MCPRequestContext(self.actor, "developer", "development", request_id)
        result = dispatch_tool("create_issue_draft", arguments, context, {"create_issue_draft": lambda **kwargs: "executed"})
        self.assertTrue(result.allowed)
        replay = dispatch_tool("create_issue_draft", arguments, context, {"create_issue_draft": lambda **kwargs: "executed"})
        self.assertFalse(replay.allowed)
        self.assertIn("consumed", replay.output)

    def test_approval_cannot_authorize_changed_arguments(self):
        original = {"title": "approved", "body": "safe"}
        pending = self._request(original)
        request_id = pending.output.split("request_id=", 1)[1]
        review_approval(request_id, reviewer=self.reviewer, approve=True)
        changed = {"title": "changed", "body": "different action"}
        context = MCPRequestContext(self.actor, "developer", "development", request_id)
        result = dispatch_tool("create_issue_draft", changed, context, {"create_issue_draft": lambda **kwargs: "executed"})
        self.assertFalse(result.allowed)
        self.assertIn("does not match", result.output)


if __name__ == "__main__":
    unittest.main()
