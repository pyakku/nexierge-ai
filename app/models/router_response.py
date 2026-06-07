from typing import Literal

from pydantic import BaseModel

RouterIntent = Literal["social", "hotel", "handoff"]


class RouterResponse(BaseModel):
    intent: RouterIntent
    reason: str
