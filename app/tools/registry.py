from dataclasses import dataclass

from app.models.brain import Brain


@dataclass
class ToolDefinition:
    name: str
    description: str


TOOLS = [
    ToolDefinition(
        name="get_answers",
        description=(
            "Search the hotel knowledge base to answer a specific question about the hotel. "
            "Call this when the guest asks about hotel facilities, services, policies, times, prices, or any hotel-specific information. "
            "Do NOT call for greetings, small talk, or questions unrelated to the hotel."
        ),
    ),
    ToolDefinition(
        name="get_media",
        description=(
            "Retrieve relevant photos or media for a hotel topic. "
            "Only call when the guest explicitly asks to see images, photos, or visual content. "
            "Do NOT call for greetings, text questions, or when no visual is requested."
        ),
    ),
    ToolDefinition(
        name="get_service_catalogs",
        description=(
            "Retrieve available service catalogs (e.g. room service, spa, laundry). "
            "Only call when the guest explicitly wants to ORDER or REQUEST a service. "
            "Do NOT call for greetings, general questions, or informational queries."
        ),
    ),
    ToolDefinition(
        name="room_details",
        description=(
            "Retrieve details about the guest's room. "
            "Only call when the guest asks specifically about rooms."
        ),
    ),
    ToolDefinition(
        name="generate_ordering_link",
        description=(
            "Generate a direct ordering link for a service catalog. "
            "Only call after get_service_catalogs has returned a service_catalog_id. "
            "Only call when the guest wants to place an order."
        ),
    ),
]

_ORDERING_LINK_PARAMS = {
    "type": "object",
    "properties": {
        "service_catalog_id": {
            "type": "string",
            "description": "ID of the service catalog returned by get_service_catalogs",
        }
    },
    "required": ["service_catalog_id"],
}

_EMPTY_PARAMS = {"type": "object", "properties": {}, "required": []}


def get_tool_definitions(brain_id: int) -> list[dict]:
    """Returns OpenAI function tool schemas for the given brain."""
    excluded: set[str] = set()
    if brain_id != Brain.GUEST_IN_STAY:
        excluded.add("generate_ordering_link")

    schemas = []
    for tool in TOOLS:
        if tool.name in excluded:
            continue
        params = (
            _ORDERING_LINK_PARAMS
            if tool.name == "generate_ordering_link"
            else _EMPTY_PARAMS
        )
        schemas.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": params,
        })

    return schemas
