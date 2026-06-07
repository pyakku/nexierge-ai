from pydantic import BaseModel, Field
from app.models.workflow_state import (
    WorkflowState,
)


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
    service_catalog_message: str | None = None
    workflow_state: (
    WorkflowState | None
) = None