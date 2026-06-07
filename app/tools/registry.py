from dataclasses import dataclass

from app.models.brain import Brain


@dataclass
class ToolDefinition:
    name: str
    description: str


TOOLS = [
    ToolDefinition(
        name="get_answers",
        description="Answer guest questions using the hotel knowledge base",
    ),
    ToolDefinition(
        name="get_media",
        description="Retrieve photos, videos and other media assets",
    ),
    ToolDefinition(
        name="get_service_catalogs",
        description=(
            "Retrieve hotel service catalogs. "
            "Returns a list of catalogs with their IDs — "
            "use the ID with generate_ordering_link."
        ),
    ),
    ToolDefinition(
        name="room_details",
        description="Retrieve room information and room details",
    ),
    ToolDefinition(
        name="generate_ordering_link",
        description=(
            "Generate an ordering link for a service catalog. "
            "Call get_service_catalogs first to obtain the service_catalog_id."
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
