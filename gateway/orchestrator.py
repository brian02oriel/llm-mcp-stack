import json
import logging
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI

from config import settings


from llm_client import build_llm_client, model_arg

llm = build_llm_client()

log = logging.getLogger(__name__)

# llm = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

# Should be a plain text, without any variable substitutions to prevent cache to break
SYSTEM_PROMPT = (
    "You are a financial analyst assistant. "
    "You must never invent, estimate or calculate figures yourself — always obtain "
    "them by calling the provided tools. If no tool can answer the question, say so "
    "plainly. Report tool results verbatim."
)


def mcp_tool_to_openai(tool: Any) -> dict:
    """Translate one MCP tool definition into OpenAI function-calling format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,   # MCP already emits JSON Schema
        },
    }


def extract_text(result: Any) -> str:
    """Flatten an MCP CallToolResult into a string for the model."""
    if getattr(result, "isError", False):
        return f"Tool error: {result.content}"
    parts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
    return "\n".join(parts) or "(tool returned no text output)"


async def fetch_tool_schemas() -> list[dict]:
    """Called once at startup. Tool definitions are stable between deployments."""
    async with streamable_http_client(settings.mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            log.info("Discovered %d MCP tools: %s", len(tools), [t.name for t in tools])
            return [mcp_tool_to_openai(t) for t in tools]


async def run_conversation(user_message: str, tool_schemas: list[dict]) -> dict:
    """The core loop: model → tool calls → results → model → ... → answer."""
    content = user_message
    if not settings.use_azure and settings.disable_thinking:
        content += " /no_think"
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]
    trace: list[dict] = []

    async with streamable_http_client(settings.mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            for turn in range(settings.max_tool_turns):
                response = await llm.chat.completions.create(
                    model=model_arg(),
                    messages=messages,
                    tools=tool_schemas,
                    tool_choice="auto",
                    temperature=0.1,
                    max_tokens=settings.max_output_tokens,
                    parallel_tool_calls=False,   # see note below
                )
                message = response.choices[0].message
                messages.append(message.model_dump(exclude_none=True))

                if not message.tool_calls:
                    return {"answer": message.content, "trace": trace, "turns": turn + 1}

                for call in message.tool_calls:
                    name = call.function.name
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        # Small models occasionally emit malformed JSON. Tell the model
                        # rather than crashing — it usually recovers on the next turn.
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": "Error: arguments were not valid JSON. Retry.",
                        })
                        continue

                    log.info("→ %s(%s)", name, args)
                    result = await session.call_tool(name, args)
                    text = extract_text(result)
                    trace.append({"tool": name, "args": args, "result": text})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": text,
                    })

    return {
        "answer": "Reached the tool-call limit without producing a final answer.",
        "trace": trace,
        "turns": settings.max_tool_turns,
    }