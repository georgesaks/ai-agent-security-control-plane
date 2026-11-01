"""Shared reviewer registry for the single and dual approval workflows.

Both workflows used to keep their own hard-coded allowlist. They now consult
this one registry. The defaults are unchanged, so existing behavior is
preserved; an integrator embedding the control plane can replace the set of
authorized reviewers with configure_reviewers().

Membership is checked both when a reviewer approves and again when the
approval is consumed, so removing a reviewer also invalidates approvals they
gave that have not been used yet.
"""

from __future__ import annotations

from typing import Iterable


DEFAULT_AUTHORIZED_REVIEWERS = frozenset({
    "security-reviewer-saki",
    "security-reviewer-primary",
    "security-reviewer-secondary",
})

_reviewers: set[str] = set(DEFAULT_AUTHORIZED_REVIEWERS)


def configure_reviewers(reviewers: Iterable[str]) -> None:
    """Replace the set of authorized reviewers."""
    names = set(reviewers)
    if not names:
        raise ValueError("at least one authorized reviewer is required")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("reviewer names must be non-empty strings")
    _reviewers.clear()
    _reviewers.update(names)


def reset_reviewers() -> None:
    """Restore the default reviewer set."""
    _reviewers.clear()
    _reviewers.update(DEFAULT_AUTHORIZED_REVIEWERS)


def authorized_reviewers() -> frozenset[str]:
    return frozenset(_reviewers)


def is_authorized_reviewer(name: str | None) -> bool:
    return name in _reviewers
