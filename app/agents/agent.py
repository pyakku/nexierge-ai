from app.brains.router import get_brain_name
from app.core.message_builder import build_messages
from app.core.prompt_loader import load_prompt
from app.models.agent_response import AgentResponse
from app.models.chat_request import ChatRequest
from app.core.llm import generate


class Agent:

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        brain = get_brain_name(
            request.brain_id
        )

        system_prompt = load_prompt(
            brain
        )

        messages = build_messages(
            request,
            system_prompt,
        )

        response_text = generate(
            [
                message.model_dump()
                for message in messages
            ]
        )

        return AgentResponse(
            response=response_text,
        )