from pydantic import BaseModel, Field


class RouterResponse(BaseModel):
    intent: str
    tools: list[str] = Field(
        default_factory=list
    )
    reason: str