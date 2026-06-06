from pydantic import BaseModel, Field


class ServiceCatalog(BaseModel):
    link: str
    message: str
    image: str


class AgentResponse(BaseModel):
    response: str
    handoff: bool = False
    media: list[str] = Field(default_factory=list)
    is_confirmation: bool = False
    suggested_question: str | None = None
    service_catalog: ServiceCatalog | None = None
    data_used: list[str] = Field(default_factory=list)