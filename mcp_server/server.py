"""Minimal MCP server for Phase 2.

This server intentionally exposes only safe, local test tools. No cloud,
GitHub write, secret, or production capability is included yet.
"""

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("ai-agent-security-control-plane")


@mcp.tool()
def read_repository_summary() -> str:
    """Return a static summary for the approved test repository."""
    return "Approved repository summary returned by the MCP test server."


@mcp.tool()
def create_issue_draft(title: str, body: str) -> str:
    """Create a local issue draft without writing to GitHub."""
    clean_title = title.strip()
    clean_body = body.strip()

    return (
        "Local issue draft created. "
        f"Title={clean_title!r}; Body length={len(clean_body)} characters. "
        "No GitHub write was performed."
    )


if __name__ == "__main__":
    mcp.run()
