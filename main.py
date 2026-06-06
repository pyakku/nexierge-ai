from app.agents.hotel_agent import HotelAgent

agent = HotelAgent()

response = agent.respond(
    "What time is breakfast?"
)

print(response.model_dump_json(indent=2))