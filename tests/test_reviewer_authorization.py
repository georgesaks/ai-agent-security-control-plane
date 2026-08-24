import unittest

from approval.workflow import clear_approvals, consume_approval, create_approval_request, review_approval


class ReviewerAuthorizationTests(unittest.TestCase):
    def setUp(self):
        clear_approvals()
        self.action = dict(
            actor="llm-agent-reviewer-lab",
            role="developer",
            environment="development",
            tool_name="create_issue_draft",
            arguments={"title": "Sensitive action", "body": "Reviewed content"},
        )

    def _request(self):
        return create_approval_request(**self.action)

    def test_authorized_reviewer_can_approve(self):
        req = self._request()
        review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True)
        allowed, detail = consume_approval(req.request_id, **self.action)
        self.assertTrue(allowed)
        self.assertIn("security-reviewer-saki", detail)

    def test_unauthorized_reviewer_cannot_approve(self):
        req = self._request()
        with self.assertRaisesRegex(PermissionError, "not authorized"):
            review_approval(req.request_id, reviewer="random-developer", approve=True)

    def test_fabricated_reviewer_cannot_approve(self):
        req = self._request()
        with self.assertRaises(PermissionError):
            review_approval(req.request_id, reviewer="security-reviewer-fake", approve=True)

    def test_requesting_actor_cannot_self_approve(self):
        action = dict(self.action)
        action["actor"] = "security-reviewer-saki"
        req = create_approval_request(**action)
        with self.assertRaisesRegex(PermissionError, "own action"):
            review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True)

    def test_failed_unauthorized_review_does_not_destroy_request(self):
        req = self._request()
        with self.assertRaises(PermissionError):
            review_approval(req.request_id, reviewer="random-developer", approve=True)
        review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True)
        allowed, _ = consume_approval(req.request_id, **self.action)
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
