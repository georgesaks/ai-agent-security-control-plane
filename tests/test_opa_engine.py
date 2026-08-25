import unittest

from policy.engine import CRITICAL, READ_ONLY, SENSITIVE, UNKNOWN, PolicyContext
from policy.opa_engine import evaluate_opa


class OPAEngineTests(unittest.TestCase):
    def test_opa_allows_developer_read(self):
        decision = evaluate_opa(PolicyContext(
            "opa-engine-agent", "developer", "development", "read_repository_summary"
        ))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action_classification, READ_ONLY)

    def test_opa_classifies_sensitive_action(self):
        decision = evaluate_opa(PolicyContext(
            "opa-engine-agent", "developer", "development", "create_issue_draft"
        ))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action_classification, SENSITIVE)

    def test_opa_classifies_critical_action(self):
        decision = evaluate_opa(PolicyContext(
            "opa-engine-agent", "developer", "development", "critical_configuration_change"
        ))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action_classification, CRITICAL)

    def test_opa_denies_production_sensitive_action(self):
        decision = evaluate_opa(PolicyContext(
            "opa-engine-agent", "developer", "production", "create_issue_draft"
        ))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action_classification, SENSITIVE)

    def test_missing_opa_binary_fails_closed(self):
        decision = evaluate_opa(
            PolicyContext("opa-engine-agent", "developer", "development", "read_repository_summary"),
            opa_binary="Z:/definitely-not-present/opa.exe",
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action_classification, UNKNOWN)
        self.assertIn("fail-closed", decision.reason)

    def test_invalid_policy_fails_closed(self):
        decision = evaluate_opa(
            PolicyContext("opa-engine-agent", "developer", "development", "read_repository_summary"),
            policy_path=__import__("pathlib").Path("definitely-missing-policy.rego"),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action_classification, UNKNOWN)
        self.assertIn("fail-closed", decision.reason)


if __name__ == "__main__":
    unittest.main()
