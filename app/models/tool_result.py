from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    knowledge_context: str = ""
    media_context: str = ""
    ordering_context: str = ""
    service_catalog_id: str | None = None
    ordering_link: str | None = None
    media: list[str] = Field(
        default_factory=list
    )
