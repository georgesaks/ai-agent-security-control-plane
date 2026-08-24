import unittest
from datetime import datetime, timedelta, timezone

from approval.workflow import (
    clear_approvals,
    consume_approval,
    create_approval_request,
    review_approval,
)


class ApprovalExpirationTests(unittest.TestCase):
    def setUp(self):
        clear_approvals()
        self.now = datetime(2026, 8, 24, 22, 0, tzinfo=timezone.utc)
        self.kwargs = dict(
            actor="llm-agent-expiration-lab",
            role="developer",
            environment="development",
            tool_name="create_issue_draft",
            arguments={"title": "Reviewed", "body": "Exact content"},
        )

    def test_fresh_approved_request_is_allowed(self):
        req = create_approval_request(**self.kwargs, ttl_seconds=300, now=self.now)
        review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True,
                        now=self.now + timedelta(seconds=10))
        allowed, _ = consume_approval(req.request_id, **self.kwargs,
                                      now=self.now + timedelta(seconds=60))
        self.assertTrue(allowed)

    def test_approved_request_expires_before_execution(self):
        req = create_approval_request(**self.kwargs, ttl_seconds=300, now=self.now)
        review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True,
                        now=self.now + timedelta(seconds=10))
        allowed, detail = consume_approval(req.request_id, **self.kwargs,
                                           now=self.now + timedelta(seconds=301))
        self.assertFalse(allowed)
        self.assertIn("expired", detail)

    def test_pending_request_cannot_be_approved_after_expiration(self):
        req = create_approval_request(**self.kwargs, ttl_seconds=300, now=self.now)
        with self.assertRaisesRegex(ValueError, "expired"):
            review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True,
                            now=self.now + timedelta(seconds=301))

    def test_expired_request_remains_denied(self):
        req = create_approval_request(**self.kwargs, ttl_seconds=60, now=self.now)
        review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True,
                        now=self.now + timedelta(seconds=5))
        first, _ = consume_approval(req.request_id, **self.kwargs,
                                    now=self.now + timedelta(seconds=61))
        second, detail = consume_approval(req.request_id, **self.kwargs,
                                          now=self.now + timedelta(seconds=62))
        self.assertFalse(first)
        self.assertFalse(second)
        self.assertIn("expired", detail)


if __name__ == "__main__":
    unittest.main()
