from app.core.llm import generate
from app.models.agent_response import AgentResponse
from app.models.openai_message import OpenAIMessage


class ResponseGenerator:

    def generate(
        self,
        messages: list[OpenAIMessage],
    ) -> AgentResponse:

        return generate(
            [
                message.model_dump()
                for message in messages
            ]
        )