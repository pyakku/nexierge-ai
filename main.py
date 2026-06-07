# from app.agents.agent import Agent
# from app.models.brain import Brain
# from app.models.chat_request import ChatRequest

# agent = Agent()

# request = ChatRequest(
#     hotel_name="Demo Hotel",
#     query="What time is breakfast?",
#     sandbox="",
#     hotel_id="c7be33f2-56cc-42ff-a36d-5f4d6a541354",
#     phone_number="",
#     tone="friendly",
#     message_history=[],
#     guest_stay_id="",
#     brain_id=Brain.GENERAL,
# )

# response = agent.respond(
#     request
# )

# print(
#     response.model_dump_json(
#         indent=2
#     )
# )

import os
import uuid

from fastapi import FastAPI, Request

from app.api.chat import router as chat_router
from app.core.context import correlation_id
from app.core.logging_config import setup as setup_logging

setup_logging(level=os.getenv("LOG_LEVEL", "DEBUG"))

app = FastAPI(title="Nexierge AI")


@app.middleware("http")
async def correlation_id_middleware(
    request: Request,
    call_next,
):
    cid = request.headers.get(
        "X-Correlation-ID", str(uuid.uuid4())
    )
    correlation_id.set(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


app.include_router(chat_router)