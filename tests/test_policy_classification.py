import unittest

from policy.engine import (
    CRITICAL,
    READ_ONLY,
    SENSITIVE,
    UNKNOWN,
    PolicyContext,
    classify_action,
    evaluate,
)


class PolicyClassificationTests(unittest.TestCase):
    def test_repository_read_is_read_only(self):
        self.assertEqual(classify_action("read_repository_summary"), READ_ONLY)

    def test_issue_draft_is_sensitive(self):
        self.assertEqual(classify_action("create_issue_draft"), SENSITIVE)

    def test_configuration_change_is_critical(self):
        self.assertEqual(classify_action("critical_configuration_change"), CRITICAL)

    def test_unknown_tool_is_unclassified(self):
        self.assertEqual(classify_action("totally_unknown_tool"), UNKNOWN)

    def test_policy_decision_carries_classification(self):
        decision = evaluate(PolicyContext(
            actor="classification-test-agent",
            role="developer",
            environment="development",
            tool_name="create_issue_draft",
        ))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action_classification, SENSITIVE)

    def test_production_sensitive_action_is_denied_by_classification(self):
        decision = evaluate(PolicyContext(
            actor="classification-test-agent",
            role="developer",
            environment="production",
            tool_name="create_issue_draft",
        ))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action_classification, SENSITIVE)

    def test_production_critical_action_is_denied_by_classification(self):
        decision = evaluate(PolicyContext(
            actor="classification-test-agent",
            role="developer",
            environment="production",
            tool_name="critical_configuration_change",
        ))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action_classification, CRITICAL)


if __name__ == "__main__":
    unittest.main()
