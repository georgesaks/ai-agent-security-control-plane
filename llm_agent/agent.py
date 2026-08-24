"""First real LLM agent for the security control plane lab.

The model may choose a tool, but it never receives trusted role claims or the
identity signing secret. Tool execution still passes through verified identity,
policy enforcement, and audit telemetry.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from identity.agent_identity import issue_token
from mcp_server.server import _secured_call


MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")

TOOLS = [
    {
        "type": "function",
        "name": "read_repository_summary",
        "description": "Read a short summary of the approved test repository.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "create_issue_draft",
        "description": "Create a local issue draft. This does not write to GitHub.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["title", "body"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def execute_model_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    identity_token: str,
    environment: str,
) -> str:
    """Send a model-selected action through the existing security boundary."""
    if tool_name == "read_repository_summary":
        return _secured_call(
            tool_name,
            identity_token=identity_token,
            environment=environment,
        )

    if tool_name == "create_issue_draft":
        return _secured_call(
            tool_name,
            identity_token=identity_token,
            environment=environment,
            arguments=arguments,
        )

    # A model-generated or unexpected tool name still reaches default deny.
    return _secured_call(
        tool_name,
        identity_token=identity_token,
        environment=environment,
        arguments=arguments,
    )


def run_agent(
    user_request: str,
    *,
    actor: str = "llm-agent-001",
    role: str = "developer",
    environment: str = "development",
) -> str:
    signing_secret = os.environ.get("AGENT_IDENTITY_SIGNING_SECRET")
    if not signing_secret:
        return "DENIED: agent identity signing is not configured"

    identity_token = issue_token(
        actor=actor,
        role=role,
        signing_secret=signing_secret,
        ttl_seconds=300,
    )

    client = OpenAI()
    input_items: list[Any] = [{"role": "user", "content": user_request}]

    response = client.responses.create(
        model=MODEL,
        instructions=(
            "You are a constrained repository assistant. Use tools only when "
            "they are useful for the user's request. Never claim that a tool "
            "succeeded unless you receive a successful tool result."
        ),
        tools=TOOLS,
        input=input_items,
    )

    # Preserve the model output before appending function results, as required
    # for multi-step Responses API tool calling.
    input_items += response.output

    tool_calls = [item for item in response.output if item.type == "function_call"]
    if not tool_calls:
        return response.output_text

    for call in tool_calls:
        arguments = json.loads(call.arguments)
        tool_result = execute_model_tool(
            tool_name=call.name,
            arguments=arguments,
            identity_token=identity_token,
            environment=environment,
        )
        input_items.append(
            {
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": tool_result,
            }
        )

    final_response = client.responses.create(
        model=MODEL,
        instructions=(
            "Report the result accurately. If the security control plane denied "
            "a requested action, clearly say that it was denied."
        ),
        tools=TOOLS,
        input=input_items,
    )
    return final_response.output_text


if __name__ == "__main__":
    print(run_agent("Read the approved repository summary."))
