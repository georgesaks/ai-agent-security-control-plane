"""Tests for trusted agent identity claims."""

import unittest
from unittest.mock import patch

from identity.agent_identity import IdentityError, issue_token, verify_token


TEST_SECRET = "local-test-signing-secret"


class AgentIdentityTests(unittest.TestCase):
    def test_valid_signed_identity_is_verified(self) -> None:
        token = issue_token(
            actor="agent-001",
            role="developer",
            signing_secret=TEST_SECRET,
        )

        identity = verify_token(token, signing_secret=TEST_SECRET)

        self.assertEqual(identity.actor, "agent-001")
        self.assertEqual(identity.role, "developer")

    def test_tampered_claims_fail_signature_verification(self) -> None:
        token = issue_token(
            actor="agent-002",
            role="auditor",
            signing_secret=TEST_SECRET,
        )
        payload, signature = token.split(".", 1)
        tampered_token = f"{payload[:-1]}A.{signature}"

        with self.assertRaises(IdentityError):
            verify_token(tampered_token, signing_secret=TEST_SECRET)

    def test_wrong_signing_secret_is_rejected(self) -> None:
        token = issue_token(
            actor="agent-003",
            role="developer",
            signing_secret=TEST_SECRET,
        )

        with self.assertRaises(IdentityError):
            verify_token(token, signing_secret="attacker-secret")

    @patch("identity.agent_identity.time.time", return_value=1_000)
    def test_expired_identity_is_rejected(self, _mock_time) -> None:
        token = issue_token(
            actor="agent-004",
            role="developer",
            signing_secret=TEST_SECRET,
            ttl_seconds=-1,
        )

        with self.assertRaises(IdentityError):
            verify_token(token, signing_secret=TEST_SECRET)


if __name__ == "__main__":
    unittest.main()
