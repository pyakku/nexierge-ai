from app.agents.agent import Agent
from app.models.brain import Brain
from app.models.chat_request import ChatRequest

agent = Agent()

request = ChatRequest(
    hotel_name="Demo Hotel",
    guest_language="English",
    query="What time is breakfast?",
    sandbox="",
    hotel_id="c7be33f2-56cc-42ff-a36d-5f4d6a541354",
    phone_number="",
    tone="friendly",
    message_history=[],
    guest_stay_id="",
    brain_id=Brain.GENERAL,
)

response = agent.respond(
    request
)

print(
    response.model_dump_json(
        indent=2
    )
)