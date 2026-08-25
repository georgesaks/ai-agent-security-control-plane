"""Adversarial tests for the OPA-backed gateway enforcement boundary."""

import unittest
from unittest.mock import patch

from mcp_server.gateway import MCPRequestContext, dispatch_tool
from policy.engine import PolicyDecision
from response.containment import clear_containment
from risk.adaptive_risk import reset_risk


class OPAEnforcementBoundaryTests(unittest.TestCase):
    actor = "opa-boundary-attack-agent"

    def setUp(self):
        clear_containment(self.actor)
        reset_risk(self.actor)
        self.registry = {
            "read_repository_summary": lambda **kwargs: "repository summary executed",
            "create_issue_draft": lambda **kwargs: "issue draft executed",
            "critical_configuration_change": lambda **kwargs: "critical change executed",
        }

    def tearDown(self):
        clear_containment(self.actor)
        reset_risk(self.actor)

    def dispatch(self, tool_name, *, role="developer", environment="development"):
        return dispatch_tool(
            tool_name,
            {},
            MCPRequestContext(self.actor, role, environment),
            self.registry,
        )

    def test_unknown_role_is_denied_by_opa_at_gateway(self):
        result = self.dispatch("read_repository_summary", role="administrator")
        self.assertFalse(result.allowed)
        self.assertIn("not allowed", result.output)
        self.assertIn('"decision": "DENY"', result.audit_json)

    def test_auditor_cannot_escalate_to_sensitive_action(self):
        result = self.dispatch("create_issue_draft", role="auditor")
        self.assertFalse(result.allowed)
        self.assertIn("not allowed", result.output)

    def test_production_sensitive_action_is_denied_before_approval(self):
        result = self.dispatch("create_issue_draft", environment="production")
        self.assertFalse(result.allowed)
        self.assertIn("blocked in production", result.output)
        self.assertNotIn("request_id=", result.output)

    def test_production_critical_action_is_denied_before_dual_approval(self):
        result = self.dispatch("critical_configuration_change", environment="production")
        self.assertFalse(result.allowed)
        self.assertIn("blocked in production", result.output)
        self.assertNotIn("request_id=", result.output)

    def test_unregistered_tool_is_denied_before_policy_evaluation(self):
        result = dispatch_tool(
            "attacker_supplied_tool",
            {},
            MCPRequestContext(self.actor, "developer", "development"),
            self.registry,
        )
        self.assertFalse(result.allowed)
        self.assertIn("not registered", result.output)

    @patch("mcp_server.gateway.evaluate_opa")
    def test_opa_unavailable_denial_prevents_tool_execution(self, mock_evaluate):
        executed = {"value": False}

        def handler(**kwargs):
            executed["value"] = True
            return "should never execute"

        mock_evaluate.return_value = PolicyDecision(
            False,
            "OPA policy engine unavailable; denied by fail-closed policy",
            "UNKNOWN",
        )
        result = dispatch_tool(
            "read_repository_summary",
            {},
            MCPRequestContext(self.actor, "developer", "development"),
            {"read_repository_summary": handler},
        )
        self.assertFalse(result.allowed)
        self.assertFalse(executed["value"])
        self.assertIn("fail-closed", result.output)
        self.assertIn('"decision": "DENY"', result.audit_json)

    @patch("mcp_server.gateway.evaluate_opa")
    def test_invalid_opa_decision_denial_prevents_tool_execution(self, mock_evaluate):
        executed = {"value": False}

        def handler(**kwargs):
            executed["value"] = True
            return "should never execute"

        mock_evaluate.return_value = PolicyDecision(
            False,
            "OPA returned an invalid decision; denied by fail-closed policy",
            "UNKNOWN",
        )
        result = dispatch_tool(
            "read_repository_summary",
            {},
            MCPRequestContext(self.actor, "developer", "development"),
            {"read_repository_summary": handler},
        )
        self.assertFalse(result.allowed)
        self.assertFalse(executed["value"])
        self.assertIn("invalid decision", result.output)


if __name__ == "__main__":
    unittest.main()
