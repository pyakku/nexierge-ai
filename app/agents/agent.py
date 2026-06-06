from app.brains.router import get_brain_name
from app.models.agent_response import AgentResponse
from app.models.chat_request import ChatRequest
from app.core.prompt_loader import load_prompt


class Agent:

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        brain = get_brain_name(
            request.brain_id
        )

        prompt = load_prompt(
            brain
        )
    
        return AgentResponse(
            response=prompt
        )