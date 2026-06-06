from app.agents.hotel_agent import HotelAgent
from app.models.chat_request import ChatRequest
from app.models.message import Message


agent = HotelAgent()

request = ChatRequest(
    hotel_name="Nexierge Hotel",
    guest_language="English",
    query="What time is breakfast?",
    sandbox="",
    hotel_id="123",
    phone_number="+919999999999",
    tone="friendly",
    guest_stay_id="stay_123",
    brain_id="brain_001",
    message_history=[
        Message(
            message="Hi",
            created_at=1780716319351,
            ai_response=False,
        )
    ],
)

response = agent.respond(request)

print(response.model_dump_json(indent=2))