from app.models.agent_response import AgentResponse


class HotelAgent:
    def respond(self, message: str) -> AgentResponse:
        return AgentResponse(
            response=f"You said: {message}",
            handoff=False,
            media=[],
            is_confirmation=False,
            suggested_question=None,
            service_catalog=None,
            data_used=[],
        )