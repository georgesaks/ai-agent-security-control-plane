"""Adaptive risk scoring for autonomous AI agents.

Risk is derived from observable security events, not model self-assessment.
The score drives progressive controls from monitoring through quarantine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskState:
    actor: str
    score: int
    level: str


_SCORES: dict[str, int] = {}


def _level(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def get_risk(actor: str) -> RiskState:
    score = _SCORES.get(actor, 0)
    return RiskState(actor=actor, score=score, level=_level(score))


def add_risk(actor: str, points: int) -> RiskState:
    if points < 0:
        raise ValueError("risk points must be non-negative")
    _SCORES[actor] = min(100, _SCORES.get(actor, 0) + points)
    return get_risk(actor)


def reduce_risk(actor: str, points: int) -> RiskState:
    if points < 0:
        raise ValueError("risk points must be non-negative")
    _SCORES[actor] = max(0, _SCORES.get(actor, 0) - points)
    return get_risk(actor)


def reset_risk(actor: str) -> None:
    _SCORES.pop(actor, None)


def risk_for_denied_production_write(actor: str) -> RiskState:
    """A denied production write is a strong behavioral risk signal."""
    return add_risk(actor, 30)
