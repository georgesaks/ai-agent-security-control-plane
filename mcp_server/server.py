"""Identity-aware, policy-enforced MCP server for Phase 2."""

import os

from mcp.server.fastmcp import FastMCP

from identity.agent_identity import IdentityError, verify_token
from mcp_server.gateway import MCPRequestContext, dispatch_tool


mcp = FastMCP("ai-agent-security-control-plane")


def _read_repository_summary() -> str:
    return "Approved repository summary returned by the MCP test server."


def _create_issue_draft(title: str, body: str) -> str:
    clean_title = title.strip()
    clean_body = body.strip()
    return (
        "Local issue draft created. "
        f"Title={clean_title!r}; Body length={len(clean_body)} characters. "
        "No GitHub write was performed."
    )


TOOL_REGISTRY = {
    "read_repository_summary": _read_repository_summary,
    "create_issue_draft": _create_issue_draft,
}


def _secured_call(
    tool_name: str,
    *,
    identity_token: str,
    environment: str,
    arguments: dict | None = None,
) -> str:
    signing_secret = os.environ.get("AGENT_IDENTITY_SIGNING_SECRET")
    if not signing_secret:
        return "DENIED: identity verifier is not configured; failing closed"

    try:
        identity = verify_token(identity_token, signing_secret=signing_secret)
    except IdentityError as exc:
        return f"DENIED: untrusted agent identity ({exc})"

    result = dispatch_tool(
        tool_name=tool_name,
        arguments=arguments or {},
        context=MCPRequestContext(
            actor=identity.actor,
            role=identity.role,
            environment=environment,
        ),
        tool_registry=TOOL_REGISTRY,
    )

    status = "ALLOWED" if result.allowed else "DENIED"
    return f"{status}: {result.output}\nAUDIT: {result.audit_json}"


@mcp.tool()
def read_repository_summary(
    identity_token: str,
    environment: str = "development",
) -> str:
    """Read the approved repository using verified agent identity claims."""
    return _secured_call(
        "read_repository_summary",
        identity_token=identity_token,
        environment=environment,
    )


@mcp.tool()
def create_issue_draft(
    title: str,
    body: str,
    identity_token: str,
    environment: str = "development",
) -> str:
    """Create a local issue draft using verified agent identity claims."""
    return _secured_call(
        "create_issue_draft",
        identity_token=identity_token,
        environment=environment,
        arguments={"title": title, "body": body},
    )


if __name__ == "__main__":
    mcp.run()
