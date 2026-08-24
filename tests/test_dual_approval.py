import unittest
from datetime import datetime, timedelta, timezone

from approval.dual_workflow import (
    approve_dual_request,
    clear_dual_approvals,
    consume_dual_approval,
    create_dual_approval_request,
)


class DualApprovalTests(unittest.TestCase):
    def setUp(self):
        clear_dual_approvals()
        self.now = datetime(2026, 8, 24, 23, 0, tzinfo=timezone.utc)
        self.action = dict(
            actor="llm-agent-critical-lab",
            role="developer",
            environment="development",
            tool_name="critical_configuration_change",
            arguments={"target": "security-control", "mode": "enforced"},
        )

    def _request(self):
        return create_dual_approval_request(**self.action, now=self.now)

    def test_one_reviewer_is_insufficient(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        allowed, detail = consume_dual_approval(req.request_id, **self.action, now=self.now)
        self.assertFalse(allowed)
        self.assertIn("two distinct", detail)

    def test_same_reviewer_cannot_approve_twice(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        with self.assertRaisesRegex(PermissionError, "same reviewer"):
            approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)

    def test_unauthorized_second_reviewer_is_denied(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        with self.assertRaisesRegex(PermissionError, "not authorized"):
            approve_dual_request(req.request_id, reviewer="random-developer", now=self.now)

    def test_two_distinct_authorized_reviewers_allow_exact_action(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        approve_dual_request(req.request_id, reviewer="security-reviewer-secondary", now=self.now)
        allowed, detail = consume_dual_approval(req.request_id, **self.action, now=self.now)
        self.assertTrue(allowed)
        self.assertIn("security-reviewer-primary", detail)
        self.assertIn("security-reviewer-secondary", detail)

    def test_requester_cannot_be_reviewer(self):
        action = dict(self.action)
        action["actor"] = "security-reviewer-primary"
        req = create_dual_approval_request(**action, now=self.now)
        with self.assertRaisesRegex(PermissionError, "own critical action"):
            approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)

    def test_modified_action_is_denied_after_two_approvals(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        approve_dual_request(req.request_id, reviewer="security-reviewer-secondary", now=self.now)
        changed = dict(self.action)
        changed["arguments"] = {"target": "security-control", "mode": "disabled"}
        allowed, detail = consume_dual_approval(req.request_id, **changed, now=self.now)
        self.assertFalse(allowed)
        self.assertIn("does not match", detail)

    def test_expired_dual_approval_is_denied(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        approve_dual_request(req.request_id, reviewer="security-reviewer-secondary", now=self.now)
        allowed, detail = consume_dual_approval(
            req.request_id, **self.action, now=self.now + timedelta(seconds=301)
        )
        self.assertFalse(allowed)
        self.assertIn("expired", detail)

    def test_consumed_dual_approval_cannot_be_replayed(self):
        req = self._request()
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary", now=self.now)
        approve_dual_request(req.request_id, reviewer="security-reviewer-secondary", now=self.now)
        first, _ = consume_dual_approval(req.request_id, **self.action, now=self.now)
        second, detail = consume_dual_approval(req.request_id, **self.action, now=self.now)
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertIn("two distinct", detail)


if __name__ == "__main__":
    unittest.main()
