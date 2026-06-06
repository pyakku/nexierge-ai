from app.core.openai_client import client
from app.models.agent_response import AgentResponse


def generate(
    messages: list[dict],
) -> AgentResponse:

    response = client.responses.parse(
        model="gpt-5-mini",
        input=messages,
        text_format=AgentResponse,
    )

    return response.output_parsed

