from pydantic import BaseModel


class KnowledgeItem(BaseModel):
    id: str
    question: str
    text: str
    source: str | None = None
    folder_path: str | None = None