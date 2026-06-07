from pydantic import BaseModel


class WorkflowState(BaseModel):
    workflow: str
    status: str