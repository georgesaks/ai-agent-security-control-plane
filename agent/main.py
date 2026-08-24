"""First agent prototype.

There is no LLM or external API in this version. That is deliberate. This
step isolates the basic security boundary: a request can only invoke a tool
that has explicitly been exposed to the agent.
"""

from agent.tools import list_available_tools


def run_tool(tool_name: str) -> str:
    tools = list_available_tools()

    if tool_name not in tools:
        return f"DENIED: tool '{tool_name}' is not available to this agent."

    tool = tools[tool_name]
    return f"ALLOWED: {tool.name}\nRESULT: {tool.handler()}"


def main() -> None:
    print("AI Agent Security Control Plane - Prototype 1")
    print("Available tools:")

    tools = list_available_tools()
    for tool in tools.values():
        print(f"  - {tool.name}: {tool.description}")

    print("\nTest 1: approved action")
    print(run_tool("read_repository_summary"))

    print("\nTest 2: unapproved action")
    print(run_tool("delete_repository"))


if __name__ == "__main__":
    main()
