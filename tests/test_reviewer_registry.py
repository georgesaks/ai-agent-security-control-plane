import unittest

from approval.dual_workflow import (
    approve_dual_request,
    clear_dual_approvals,
    consume_dual_approval,
    create_dual_approval_request,
)
from approval.reviewers import (
    DEFAULT_AUTHORIZED_REVIEWERS,
    authorized_reviewers,
    configure_reviewers,
    reset_reviewers,
)
from approval.workflow import clear_approvals, consume_approval, create_approval_request, review_approval


class ReviewerRegistryTests(unittest.TestCase):
    def setUp(self):
        reset_reviewers()
        clear_approvals()
        clear_dual_approvals()
        self.action = dict(
            actor="llm-agent-registry-lab",
            role="developer",
            environment="development",
            tool_name="critical_configuration_change",
            arguments={"setting": "max_connections", "value": 50},
        )

    def tearDown(self):
        reset_reviewers()

    def test_defaults_are_unchanged(self):
        self.assertEqual(authorized_reviewers(), DEFAULT_AUTHORIZED_REVIEWERS)
        self.assertIn("security-reviewer-saki", authorized_reviewers())

    def test_configured_reviewers_apply_to_single_approval(self):
        configure_reviewers({"facilities-reviewer-a"})
        req = create_approval_request(**self.action)
        with self.assertRaisesRegex(PermissionError, "not authorized"):
            review_approval(req.request_id, reviewer="security-reviewer-saki", approve=True)
        review_approval(req.request_id, reviewer="facilities-reviewer-a", approve=True)
        allowed, _ = consume_approval(req.request_id, **self.action)
        self.assertTrue(allowed)

    def test_configured_reviewers_apply_to_dual_approval(self):
        configure_reviewers({"facilities-reviewer-a", "security-reviewer-b"})
        req = create_dual_approval_request(**self.action)
        approve_dual_request(req.request_id, reviewer="facilities-reviewer-a")
        approve_dual_request(req.request_id, reviewer="security-reviewer-b")
        allowed, detail = consume_dual_approval(req.request_id, **self.action)
        self.assertTrue(allowed)
        self.assertIn("facilities-reviewer-a", detail)

    def test_removing_a_reviewer_invalidates_their_unused_approval(self):
        configure_reviewers({"facilities-reviewer-a", "security-reviewer-b"})
        req = create_approval_request(**self.action)
        review_approval(req.request_id, reviewer="facilities-reviewer-a", approve=True)
        configure_reviewers({"security-reviewer-b"})
        allowed, detail = consume_approval(req.request_id, **self.action)
        self.assertFalse(allowed)
        self.assertIn("no longer authorized", detail)

    def test_empty_or_blank_reviewer_sets_are_rejected(self):
        with self.assertRaises(ValueError):
            configure_reviewers(set())
        with self.assertRaises(ValueError):
            configure_reviewers({" "})
        self.assertEqual(authorized_reviewers(), DEFAULT_AUTHORIZED_REVIEWERS)


if __name__ == "__main__":
    unittest.main()
