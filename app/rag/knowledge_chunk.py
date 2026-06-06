from pydantic import BaseModel


class KnowledgeChunk(BaseModel):
    text: str
    score: float