from fastapi import APIRouter

from app.agents.agent import Agent
from app.models.chat_request import ChatRequest

router = APIRouter()

agent = Agent()


@router.post("/chat")
def chat(
    request: ChatRequest,
):
    return agent.respond(
        request
    )