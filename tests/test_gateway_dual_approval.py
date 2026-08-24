import unittest

from approval.dual_workflow import approve_dual_request, clear_dual_approvals
from mcp_server.gateway import MCPRequestContext, dispatch_tool
from response.containment import clear_containment
from risk.adaptive_risk import reset_risk


class GatewayDualApprovalTests(unittest.TestCase):
    actor = "llm-agent-gateway-critical-lab"
    arguments = {"target": "security-control", "mode": "enforced"}

    def setUp(self):
        clear_dual_approvals()
        clear_containment(self.actor)
        reset_risk(self.actor)
        self.registry = {
            "critical_configuration_change": lambda **kwargs: f"critical change executed: {kwargs['target']}={kwargs['mode']}"
        }

    def tearDown(self):
        clear_dual_approvals()
        clear_containment(self.actor)
        reset_risk(self.actor)

    def _initial(self):
        return dispatch_tool(
            "critical_configuration_change",
            self.arguments,
            MCPRequestContext(self.actor, "developer", "development"),
            self.registry,
        )

    def test_gateway_requires_dual_approval_before_execution(self):
        result = self._initial()
        self.assertFalse(result.allowed)
        self.assertIn("two distinct authorized reviewers required", result.output)
        self.assertIn('"decision": "REQUIRE_DUAL_APPROVAL"', result.audit_json)

    def test_gateway_denies_after_only_one_approval(self):
        pending = self._initial()
        request_id = pending.output.split("request_id=", 1)[1]
        approve_dual_request(request_id, reviewer="security-reviewer-primary")
        result = dispatch_tool(
            "critical_configuration_change", self.arguments,
            MCPRequestContext(self.actor, "developer", "development", request_id),
            self.registry,
        )
        self.assertFalse(result.allowed)
        self.assertIn("two distinct", result.output)

    def test_gateway_executes_after_two_distinct_approvals(self):
        pending = self._initial()
        request_id = pending.output.split("request_id=", 1)[1]
        approve_dual_request(request_id, reviewer="security-reviewer-primary")
        approve_dual_request(request_id, reviewer="security-reviewer-secondary")
        result = dispatch_tool(
            "critical_configuration_change", self.arguments,
            MCPRequestContext(self.actor, "developer", "development", request_id),
            self.registry,
        )
        self.assertTrue(result.allowed)
        self.assertIn("critical change executed", result.output)
        self.assertIn('"decision": "ALLOW"', result.audit_json)

    def test_gateway_denies_tampered_action_after_two_approvals(self):
        pending = self._initial()
        request_id = pending.output.split("request_id=", 1)[1]
        approve_dual_request(request_id, reviewer="security-reviewer-primary")
        approve_dual_request(request_id, reviewer="security-reviewer-secondary")
        tampered = {"target": "security-control", "mode": "disabled"}
        result = dispatch_tool(
            "critical_configuration_change", tampered,
            MCPRequestContext(self.actor, "developer", "development", request_id),
            self.registry,
        )
        self.assertFalse(result.allowed)
        self.assertIn("does not match", result.output)

    def test_gateway_denies_replay_after_execution(self):
        pending = self._initial()
        request_id = pending.output.split("request_id=", 1)[1]
        approve_dual_request(request_id, reviewer="security-reviewer-primary")
        approve_dual_request(request_id, reviewer="security-reviewer-secondary")
        context = MCPRequestContext(self.actor, "developer", "development", request_id)
        first = dispatch_tool("critical_configuration_change", self.arguments, context, self.registry)
        replay = dispatch_tool("critical_configuration_change", self.arguments, context, self.registry)
        self.assertTrue(first.allowed)
        self.assertFalse(replay.allowed)


if __name__ == "__main__":
    unittest.main()
