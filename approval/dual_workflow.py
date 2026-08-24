"""Dual-control approval workflow for highest-impact AI-agent actions.

Critical actions require two distinct authorized reviewers. The requester cannot
serve as either reviewer, both approvals must refer to the same exact action,
and the request is single-use and time-bounded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Any


DEFAULT_DUAL_APPROVAL_TTL_SECONDS = 300
AUTHORIZED_REVIEWERS = {
    "security-reviewer-saki",
    "security-reviewer-primary",
    "security-reviewer-secondary",
}


@dataclass
class DualApprovalRequest:
    request_id: str
    actor: str
    role: str
    environment: str
    tool_name: str
    arguments_digest: str
    status: str
    created_at: str
    expires_at: str
    approved_by: list[str] = field(default_factory=list)


_REQUESTS: dict[str, DualApprovalRequest] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _digest(arguments: dict[str, Any]) -> str:
    canonical = json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_dual_approval_request(
    *, actor: str, role: str, environment: str, tool_name: str,
    arguments: dict[str, Any], ttl_seconds: int = DEFAULT_DUAL_APPROVAL_TTL_SECONDS,
    now: datetime | None = None,
) -> DualApprovalRequest:
    if ttl_seconds <= 0:
        raise ValueError("dual approval ttl_seconds must be positive")
    created = now or _utc_now()
    request = DualApprovalRequest(
        request_id=f"dap_{secrets.token_hex(8)}",
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
        arguments_digest=_digest(arguments),
        status="PENDING",
        created_at=created.isoformat(),
        expires_at=(created + timedelta(seconds=ttl_seconds)).isoformat(),
    )
    _REQUESTS[request.request_id] = request
    return request


def approve_dual_request(request_id: str, *, reviewer: str,
                         now: datetime | None = None) -> DualApprovalRequest:
    request = _REQUESTS[request_id]
    current = now or _utc_now()

    if request.status in {"CONSUMED", "EXPIRED", "REJECTED"}:
        raise ValueError(f"dual approval request is {request.status.lower()}")
    if current >= datetime.fromisoformat(request.expires_at):
        request.status = "EXPIRED"
        raise ValueError("dual approval request has expired")
    if reviewer not in AUTHORIZED_REVIEWERS:
        raise PermissionError("reviewer is not authorized for critical actions")
    if reviewer == request.actor:
        raise PermissionError("requesting actor cannot approve its own critical action")
    if reviewer in request.approved_by:
        raise PermissionError("the same reviewer cannot approve twice")

    request.approved_by.append(reviewer)
    request.status = "APPROVED" if len(request.approved_by) >= 2 else "PARTIALLY_APPROVED"
    return request


def consume_dual_approval(
    request_id: str, *, actor: str, role: str, environment: str,
    tool_name: str, arguments: dict[str, Any], now: datetime | None = None,
) -> tuple[bool, str]:
    request = _REQUESTS.get(request_id)
    if request is None:
        return False, "dual approval request not found"

    current = now or _utc_now()
    if current >= datetime.fromisoformat(request.expires_at):
        request.status = "EXPIRED"
        return False, "dual approval request is expired"
    if request.status != "APPROVED":
        return False, "two distinct authorized reviewers are required"
    if len(set(request.approved_by)) != 2:
        return False, "dual approval integrity check failed"
    if any(reviewer not in AUTHORIZED_REVIEWERS for reviewer in request.approved_by):
        return False, "dual approval contains unauthorized reviewer"
    if actor in request.approved_by:
        return False, "separation of duties violation"
    if (
        request.actor != actor
        or request.role != role
        or request.environment != environment
        or request.tool_name != tool_name
        or request.arguments_digest != _digest(arguments)
    ):
        return False, "dual approval does not match the requested action"

    request.status = "CONSUMED"
    return True, f"approved by {request.approved_by[0]} and {request.approved_by[1]}"


def clear_dual_approvals() -> None:
    _REQUESTS.clear()
