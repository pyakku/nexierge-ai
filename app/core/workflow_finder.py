from app.models.message import Message
from app.models.workflow_state import (
    WorkflowState,
)

_TERMINAL_STATUSES = {
    "completed",
    "handoff_success",
    "handoff_cancelled",
}


def get_active_workflow(
    messages: list[Message],
) -> WorkflowState | None:

    for message in reversed(messages):

        if not message.ai_response:
            continue

        if not message.workflow_state:
            continue

        if (
            message.workflow_state.status
            in _TERMINAL_STATUSES
        ):
            continue

        return (
            message.workflow_state
        )

    return None