"""Policy-enforced MCP server for Phase 2.

The MCP protocol exposes the tools, but the gateway remains responsible for
security decisions. Tool implementations are local and intentionally low risk.
"""

from mcp.server.fastmcp import FastMCP

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
    actor: str,
    role: str,
    environment: str,
    arguments: dict | None = None,
) -> str:
    result = dispatch_tool(
        tool_name=tool_name,
        arguments=arguments or {},
        context=MCPRequestContext(
            actor=actor,
            role=role,
            environment=environment,
        ),
        tool_registry=TOOL_REGISTRY,
    )

    status = "ALLOWED" if result.allowed else "DENIED"
    return f"{status}: {result.output}\nAUDIT: {result.audit_json}"


@mcp.tool()
def read_repository_summary(
    actor: str,
    role: str,
    environment: str = "development",
) -> str:
    """Read the approved repository summary through the security gateway."""
    return _secured_call(
        "read_repository_summary",
        actor=actor,
        role=role,
        environment=environment,
    )


@mcp.tool()
def create_issue_draft(
    title: str,
    body: str,
    actor: str,
    role: str,
    environment: str = "development",
) -> str:
    """Create a local issue draft only when policy authorizes the request."""
    return _secured_call(
        "create_issue_draft",
        actor=actor,
        role=role,
        environment=environment,
        arguments={"title": title, "body": body},
    )


if __name__ == "__main__":
    mcp.run()
