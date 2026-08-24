"""Tests for AI agent security telemetry detections."""

import unittest

from telemetry.audit import build_audit_event
from telemetry.detection import detect_event, detect_repeated_denials


class DetectionTests(unittest.TestCase):
    def _denied_prod_write(self, actor: str = "agent-1"):
        return build_audit_event(
            actor=actor,
            role="developer",
            environment="production",
            tool_name="create_issue_draft",
            decision="DENY",
            reason="write-oriented actions are blocked in production",
        )

    def test_production_denial_generates_high_alerts(self) -> None:
        findings = detect_event(self._denied_prod_write())
        rule_ids = {finding.rule_id for finding in findings}
        self.assertIn("AI-001", rule_ids)
        self.assertIn("AI-002", rule_ids)

    def test_allowed_development_read_does_not_alert(self) -> None:
        event = build_audit_event(
            actor="agent-1",
            role="developer",
            environment="development",
            tool_name="read_repository_summary",
            decision="ALLOW",
            reason="policy requirements satisfied",
        )
        self.assertEqual(detect_event(event), [])

    def test_three_denials_generate_correlated_critical_alert(self) -> None:
        events = [self._denied_prod_write("agent-repeat") for _ in range(3)]
        findings = detect_repeated_denials(events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "AI-003")
        self.assertEqual(findings[0].severity, "CRITICAL")


if __name__ == "__main__":
    unittest.main()
