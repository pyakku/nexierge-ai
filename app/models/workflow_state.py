from typing import Literal

from pydantic import BaseModel

WorkflowName = Literal["handoff"]

WorkflowStatus = Literal[
    "awaiting_confirmation",
    "handoff_success",
    "handoff_cancelled",
]


class WorkflowState(BaseModel):
    workflow: WorkflowName
    status: WorkflowStatus