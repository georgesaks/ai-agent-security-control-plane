"""Human-in-the-loop approval workflow for sensitive AI-agent actions.

Approval records are intentionally in-memory for this prototype. A request is
bound to the actor, tool, arguments, role, and environment that were reviewed,
so an approval cannot be reused for a different action. Approved requests are
time-bounded, expire automatically, and must be reviewed by an authorized
reviewer who is distinct from the requesting actor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Any


DEFAULT_APPROVAL_TTL_SECONDS = 300
AUTHORIZED_REVIEWERS = {
    "security-reviewer-saki",
    "security-reviewer-primary",
    "security-reviewer-secondary",
}


@dataclass
class ApprovalRequest:
    request_id: str
    actor: str
    role: str
    environment: str
    tool_name: str
    arguments_digest: str
    status: str
    created_at: str
    expires_at: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None


_REQUESTS: dict[str, ApprovalRequest] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def arguments_digest(arguments: dict[str, Any]) -> str:
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_approval_request(
    *,
    actor: str,
    role: str,
    environment: str,
    tool_name: str,
    arguments: dict[str, Any],
    ttl_seconds: int = DEFAULT_APPROVAL_TTL_SECONDS,
    now: datetime | None = None,
) -> ApprovalRequest:
    if ttl_seconds <= 0:
        raise ValueError("approval ttl_seconds must be positive")

    created = now or _utc_now()
    expires = created + timedelta(seconds=ttl_seconds)
    request = ApprovalRequest(
        request_id=f"apr_{secrets.token_hex(8)}",
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
        arguments_digest=arguments_digest(arguments),
        status="PENDING",
        created_at=created.isoformat(),
        expires_at=expires.isoformat(),
    )
    _REQUESTS[request.request_id] = request
    return request


def review_approval(
    request_id: str,
    *,
    reviewer: str,
    approve: bool,
    now: datetime | None = None,
) -> ApprovalRequest:
    request = _REQUESTS[request_id]
    current = now or _utc_now()

    if request.status != "PENDING":
        raise ValueError("approval request has already been reviewed")

    if current >= datetime.fromisoformat(request.expires_at):
        request.status = "EXPIRED"
        raise ValueError("approval request has expired")

    if reviewer not in AUTHORIZED_REVIEWERS:
        raise PermissionError("reviewer is not authorized to approve sensitive actions")

    if reviewer == request.actor:
        raise PermissionError("requesting actor cannot approve its own action")

    request.status = "APPROVED" if approve else "REJECTED"
    request.reviewed_by = reviewer
    request.reviewed_at = current.isoformat()
    return request


def consume_approval(
    request_id: str,
    *,
    actor: str,
    role: str,
    environment: str,
    tool_name: str,
    arguments: dict[str, Any],
    now: datetime | None = None,
) -> tuple[bool, str]:
    request = _REQUESTS.get(request_id)
    if request is None:
        return False, "approval request not found"

    current = now or _utc_now()
    if current >= datetime.fromisoformat(request.expires_at):
        request.status = "EXPIRED"
        return False, "approval request is expired"

    if request.status != "APPROVED":
        return False, f"approval request is {request.status.lower()}"

    if request.reviewed_by not in AUTHORIZED_REVIEWERS:
        return False, "approval reviewer is no longer authorized"

    if request.reviewed_by == request.actor:
        return False, "separation of duties violation"

    if (
        request.actor != actor
        or request.role != role
        or request.environment != environment
        or request.tool_name != tool_name
        or request.arguments_digest != arguments_digest(arguments)
    ):
        return False, "approval does not match the requested action"

    request.status = "CONSUMED"
    return True, f"approved by {request.reviewed_by}"


def clear_approvals() -> None:
    _REQUESTS.clear()
