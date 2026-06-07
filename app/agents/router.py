from app.core.openai_client import client
from app.models.brain import Brain
from app.models.router_response import (
    RouterResponse,
)
from app.tools.registry import (
    get_tools_prompt,
)


class Router:

    def route(
        self,
        query: str,
        brain_id: int,
    ) -> RouterResponse:

        tools_prompt = get_tools_prompt(
            brain_id
        )

        ordering_link_rule = ""

        if brain_id != Brain.GUEST_IN_STAY:
            ordering_link_rule = """
generate_ordering_link is not available for this brain.
Do not return generate_ordering_link.
"""

        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": f"""
You are a hotel concierge router.

Available intents:

GREETING
INFORMATION
ACTION
HANDOFF

Available tools:

{tools_prompt}

RULES

Return the minimum set of tools
required to fulfill the request.

Multiple tools may be returned.
For any question about rooms, use the room_details tool. Never use any other tool for room related questions.
{ordering_link_rule}

Examples:

"What time is breakfast?"

intent=INFORMATION
tools=["get_answers"]

---

"Show me pool photos"

intent=INFORMATION
tools=["get_media"]

---

"Tell me about the deluxe room"

intent=INFORMATION
tools=["room_details"]

---

"Tell me about the deluxe room and show photos"

intent=INFORMATION
tools=["room_details"]

---

"What spa services do you offer? Show pictures."

intent=INFORMATION
tools=["get_service_catalogs","get_media"]

---

"I want room service"

intent=ACTION
tools=["get_service_catalogs","generate_ordering_link"]

---

"I want to browse services"

intent=ACTION
tools=["get_service_catalogs"]

---

"I want to speak to a human"

intent=HANDOFF
tools=[]

---

"Hello"

intent=GREETING
tools=[]

Return:

intent
tools
reason
""",
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            text_format=RouterResponse,
        )

        result = response.output_parsed
        if result is None:
            raise ValueError(
                "Router LLM returned no structured output"
            )
        return result
