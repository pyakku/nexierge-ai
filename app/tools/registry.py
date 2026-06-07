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
            "Answer guest questions using the hotel knowledge base"
        ),
    ),
    ToolDefinition(
        name="get_media",
        description=(
            "Retrieve photos, videos and other media assets"
        ),
    ),
    ToolDefinition(
        name="get_service_catalogs",
        description=(
            "Retrieve hotel service catalogs and available services"
        ),
    ),
    ToolDefinition(
        name="room_details",
        description=(
            "Retrieve room information and room details"
        ),
    ),
    ToolDefinition(
        name="generate_ordering_link",
        description=(
            "Generate an ordering link for a specific service with optional pre-filled details"
        ),
    ),
]


TOOLS_PROMPT = "\n".join(
    [
        (
            f"{tool.name}: "
            f"{tool.description}"
        )
        for tool in TOOLS
    ]
)


def get_tools_prompt(
    brain_id: int,
) -> str:

    tools = TOOLS

    if brain_id != Brain.GUEST_IN_STAY:
        tools = [
            tool
            for tool in TOOLS
            if tool.name
            != "generate_ordering_link"
        ]

    return "\n".join(
        (
            f"{tool.name}: "
            f"{tool.description}"
        )
        for tool in tools
    )
