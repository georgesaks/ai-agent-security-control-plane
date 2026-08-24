"""Tests for structured authorization audit events."""

import json
import unittest

from telemetry.audit import build_audit_event


class AuditEventTests(unittest.TestCase):
    def test_audit_event_contains_security_context(self) -> None:
        event = build_audit_event(
            actor="agent-001",
            role="developer",
            environment="production",
            tool_name="create_issue_draft",
            decision="DENY",
            reason="write-oriented actions are blocked in production",
        )

        payload = json.loads(event.to_json())

        self.assertEqual(payload["actor"], "agent-001")
        self.assertEqual(payload["role"], "developer")
        self.assertEqual(payload["environment"], "production")
        self.assertEqual(payload["tool_name"], "create_issue_draft")
        self.assertEqual(payload["decision"], "DENY")
        self.assertIn("production", payload["reason"])
        self.assertTrue(payload["timestamp"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
