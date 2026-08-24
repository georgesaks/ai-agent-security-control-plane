"""Minimal tool layer for the first agent prototype.

This module intentionally keeps the tool surface small. The goal is to make
it easy to see which actions the agent can request before we introduce a
separate policy engine.
"""

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[[], str]


def read_repository_summary() -> str:
    return "Repository summary retrieved from the approved test repository."


def create_issue_draft() -> str:
    return "Issue draft created locally. No GitHub write was performed."


def list_available_tools() -> Dict[str, Tool]:
    """Return the tools exposed to the prototype agent."""
    return {
        "read_repository_summary": Tool(
            name="read_repository_summary",
            description="Read a short summary of the approved repository.",
            handler=read_repository_summary,
        ),
        "create_issue_draft": Tool(
            name="create_issue_draft",
            description="Create a local issue draft without writing to GitHub.",
            handler=create_issue_draft,
        ),
    }
