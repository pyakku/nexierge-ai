from pydantic import BaseModel

from app.models.message import Message


class ChatRequest(BaseModel):
    hotel_name: str
    guest_language: str
    query: str
    sandbox: str
    hotel_id: str
    phone_number: str
    tone: str
    message_history: list[Message]
    guest_stay_id: str
    brain_id: int