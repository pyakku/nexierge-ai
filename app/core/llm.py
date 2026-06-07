import logging
import os
from time import perf_counter

from app.core.openai_client import client
from app.models.agent_response import AgentResponse

logger = logging.getLogger(__name__)


def generate(
    messages: list[dict],
) -> AgentResponse:
    """Simple generation without tools — used for active-workflow path."""
    model = os.getenv("BRAIN_MODEL", "gpt-4o-mini")
    start = perf_counter()

    response = client.responses.parse(
        model=model,
        input=messages,
        text_format=AgentResponse,
    )

    latency = int((perf_counter() - start) * 1000)
    logger.info(
        "llm.call",
        extra={
            "model": model,
            "num_messages": len(messages),
            "result": "direct",
            "latency_ms": latency,
            "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", None),
            "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", None),
        },
    )

    result = response.output_parsed
    if result is None:
        raise ValueError("LLM returned no structured output")
    return result


def generate_with_tools(
    messages: list[dict],
    tools: list[dict],
) -> tuple[AgentResponse | None, list]:
    """
    LLM call with tool definitions.
    Returns (AgentResponse, []) when the model responds directly.
    Returns (None, tool_calls) when the model wants to call tools.
    """
    model = os.getenv("BRAIN_MODEL", "gpt-4o-mini")
    start = perf_counter()

    response = client.responses.parse(
        model=model,
        input=messages,
        text_format=AgentResponse,
        tools=tools,
    )

    tool_calls = [
        item for item in (response.output or [])
        if getattr(item, "type", None) == "function_call"
    ]

    latency = int((perf_counter() - start) * 1000)
    logger.info(
        "llm.call",
        extra={
            "model": model,
            "num_messages": len(messages),
            "result": "tool_calls" if tool_calls else "direct",
            "tool_calls": [tc.name for tc in tool_calls],
            "latency_ms": latency,
            "input_tokens": getattr(getattr(response, "usage", None), "input_tokens", None),
            "output_tokens": getattr(getattr(response, "usage", None), "output_tokens", None),
        },
    )

    if tool_calls:
        return None, tool_calls

    result = response.output_parsed
    if result is None:
        raise ValueError("LLM returned no structured output")
    return result, []
