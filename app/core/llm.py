# from app.core.openai_client import client
# from app.models.agent_response import AgentResponse


# def generate(
#     messages: list[dict],
# ) -> AgentResponse:

#     response = client.responses.parse(
#         model="gpt-5-mini",
#         input=messages,
#         text_format=AgentResponse,
#     )

#     return response.output_parsed

from app.models.agent_response import AgentResponse
from app.core.openai_client import client


def generate(
    messages: list[dict],
) -> AgentResponse:

    response = client.responses.create(
        model="gpt-5-mini",
        input=messages,
    )

    return AgentResponse(
        response=response.output_text,
        handoff=False,
        media=[],
        is_confirmation=False,
        suggested_question=None,
        service_catalog=None,
        data_used=[],
    )