"""First agent prototype with an independent authorization decision."""

from agent.tools import list_available_tools
from policy.engine import PolicyContext, evaluate


def run_tool(
    tool_name: str,
    *,
    actor: str = "local-user",
    role: str = "developer",
    environment: str = "development",
) -> str:
    tools = list_available_tools()

    if tool_name not in tools:
        return f"DENIED: tool '{tool_name}' is not available to this agent."

    context = PolicyContext(
        actor=actor,
        role=role,
        environment=environment,
        tool_name=tool_name,
    )
    decision = evaluate(context)

    if not decision.allowed:
        return f"DENIED BY POLICY: {decision.reason}"

    tool = tools[tool_name]
    return (
        f"ALLOWED BY POLICY: {tool.name}\n"
        f"ACTOR: {actor}\n"
        f"ROLE: {role}\n"
        f"ENVIRONMENT: {environment}\n"
        f"RESULT: {tool.handler()}"
    )


def main() -> None:
    print("AI Agent Security Control Plane - Prototype 2")

    print("\nTest 1: developer reads repository in development")
    print(run_tool("read_repository_summary"))

    print("\nTest 2: auditor attempts issue draft")
    print(run_tool("create_issue_draft", role="auditor"))

    print("\nTest 3: developer attempts issue draft in production")
    print(run_tool("create_issue_draft", environment="production"))


if __name__ == "__main__":
    main()
