from app.core.openai_client import client
from app.models.agent_response import AgentResponse


def generate(
    messages: list[dict],
) -> AgentResponse:

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=messages,
        text_format=AgentResponse,
    )

    result = response.output_parsed
    if result is None:
        raise ValueError(
            "LLM returned no structured output"
        )
    return result

