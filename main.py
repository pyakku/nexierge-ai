# from app.agents.agent import Agent
# from app.models.brain import Brain
# from app.models.chat_request import ChatRequest
# from app.models.message import Message


# agent = Agent()

# request = ChatRequest(
#     hotel_name="Nexierge Hotel",
#     guest_language="English",
#     query="What time is breakfast?",
#     sandbox="",
#     hotel_id="123",
#     phone_number="+919999999999",
#     tone="friendly",
#     guest_stay_id="stay_123",
#     brain_id=Brain.GENERAL,
#     message_history=[
#         Message(
#             message="Hi",
#             created_at=1780716319351,
#             ai_response=False,
#         )
#     ],
# )

# response = agent.respond(request)
# print(type(response))
# print(
#     response.model_dump_json(
#         indent=2
#     )
# )
from app.models.brain import Brain
from app.rag.retriever import Retriever


retriever = Retriever()

results = retriever.retrieve(
    query="What time is breakfast?",
    hotel_id="c7be33f2-56cc-42ff-a36d-5f4d6a541354",
    brain_id=Brain.GENERAL,
)

print(results)