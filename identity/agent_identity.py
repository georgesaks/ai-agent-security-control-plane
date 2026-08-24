"""Local signed identity tokens for the Phase 2 security lab.

This is intentionally a lab-grade identity layer. It demonstrates the trust
boundary by signing identity claims outside the agent request. A production
system would use an external identity provider and short-lived workload
credentials rather than a shared local signing secret.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import hashlib
import hmac
import json
import time
from typing import Any


@dataclass(frozen=True)
class VerifiedIdentity:
    actor: str
    role: str
    expires_at: int


class IdentityError(ValueError):
    """Raised when an agent identity token cannot be trusted."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def issue_token(
    *,
    actor: str,
    role: str,
    signing_secret: str,
    ttl_seconds: int = 300,
) -> str:
    """Issue a short-lived signed token for a lab agent identity."""
    claims = {
        "actor": actor,
        "role": role,
        "expires_at": int(time.time()) + ttl_seconds,
    }
    payload = _b64url_encode(json.dumps(claims, sort_keys=True).encode("utf-8"))
    signature = hmac.new(
        signing_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload}.{_b64url_encode(signature)}"


def verify_token(token: str, *, signing_secret: str) -> VerifiedIdentity:
    """Verify token signature and expiry, then return trusted claims."""
    try:
        payload, supplied_signature = token.split(".", 1)
    except ValueError as exc:
        raise IdentityError("malformed identity token") from exc

    expected_signature = hmac.new(
        signing_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    try:
        supplied_signature_bytes = _b64url_decode(supplied_signature)
    except Exception as exc:
        raise IdentityError("invalid identity token signature encoding") from exc

    if not hmac.compare_digest(expected_signature, supplied_signature_bytes):
        raise IdentityError("identity token signature verification failed")

    try:
        claims: dict[str, Any] = json.loads(_b64url_decode(payload).decode("utf-8"))
        actor = str(claims["actor"])
        role = str(claims["role"])
        expires_at = int(claims["expires_at"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IdentityError("identity token claims are invalid") from exc

    if expires_at <= int(time.time()):
        raise IdentityError("identity token has expired")

    return VerifiedIdentity(actor=actor, role=role, expires_at=expires_at)
