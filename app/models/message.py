from pydantic import BaseModel
from app.models.workflow_state import (
    WorkflowState,
)


class Message(BaseModel):
    message: str
    ai_response: bool
    created_at: int | None = None

    workflow_state: (
        WorkflowState | None
    ) = None