"""Parity tests between the current Python policy and shadow-mode OPA/Rego.

OPA is intentionally not the enforcement source yet. These tests prove that
Rego returns the same allow/deny and sensitivity decisions as the Python
policy before the gateway is migrated.
"""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from policy.engine import PolicyContext, evaluate


ROOT = Path(__file__).resolve().parents[1]
REGO_POLICY = ROOT / "policy" / "opa" / "agent_policy.rego"


class OPAPolicyParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.opa = shutil.which("opa")
        if cls.opa is None:
            raise unittest.SkipTest("OPA CLI is not available on PATH")

    def rego_decision(self, *, actor, role, environment, tool_name):
        payload = {
            "actor": actor,
            "role": role,
            "environment": environment,
            "tool_name": tool_name,
        }
        # Use an input file rather than stdin because this is also stable on
        # Windows PowerShell, where piped stdin caused a runtime failure during
        # manual validation.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as handle:
            json.dump(payload, handle)
            input_path = Path(handle.name)

        try:
            completed = subprocess.run(
                [
                    self.opa,
                    "eval",
                    "--format=json",
                    "--input",
                    str(input_path),
                    "--data",
                    str(REGO_POLICY),
                    "data.aiagent.authz.decision",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            document = json.loads(completed.stdout)
            return document["result"][0]["expressions"][0]["value"]
        finally:
            input_path.unlink(missing_ok=True)

    def assert_parity(self, *, role, environment, tool_name):
        actor = "opa-parity-agent"
        python_decision = evaluate(
            PolicyContext(actor, role, environment, tool_name)
        )
        rego_decision = self.rego_decision(
            actor=actor,
            role=role,
            environment=environment,
            tool_name=tool_name,
        )
        self.assertEqual(rego_decision["allowed"], python_decision.allowed)
        self.assertEqual(
            rego_decision["classification"],
            python_decision.action_classification,
        )
        self.assertEqual(rego_decision["reason"], python_decision.reason)

    def test_developer_read_only_parity(self):
        self.assert_parity(
            role="developer",
            environment="development",
            tool_name="read_repository_summary",
        )

    def test_developer_sensitive_parity(self):
        self.assert_parity(
            role="developer",
            environment="development",
            tool_name="create_issue_draft",
        )

    def test_developer_critical_parity(self):
        self.assert_parity(
            role="developer",
            environment="development",
            tool_name="critical_configuration_change",
        )

    def test_auditor_read_only_parity(self):
        self.assert_parity(
            role="auditor",
            environment="development",
            tool_name="read_repository_summary",
        )

    def test_auditor_sensitive_denial_parity(self):
        self.assert_parity(
            role="auditor",
            environment="development",
            tool_name="create_issue_draft",
        )

    def test_production_sensitive_denial_parity(self):
        self.assert_parity(
            role="developer",
            environment="production",
            tool_name="create_issue_draft",
        )

    def test_production_critical_denial_parity(self):
        self.assert_parity(
            role="developer",
            environment="production",
            tool_name="critical_configuration_change",
        )

    def test_unknown_role_denial_parity(self):
        self.assert_parity(
            role="unknown-role",
            environment="development",
            tool_name="read_repository_summary",
        )


if __name__ == "__main__":
    unittest.main()
