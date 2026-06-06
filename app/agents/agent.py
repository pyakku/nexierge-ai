from app.models.agent_response import AgentResponse
from app.models.chat_request import ChatRequest


class HotelAgent:

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        return AgentResponse(
            response=f"Received query: {request.query}",
        )