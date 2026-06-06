from app.rag.knowledge_repository import (
    KnowledgeRepository,
)
from app.rag.retriever import Retriever


class KnowledgeService:

    def __init__(self):
        self.retriever = Retriever()
        self.repository = KnowledgeRepository()

    def retrieve(
        self,
        query: str,
        hotel_id: str,
        brain_id,
    ):

        ids = self.retriever.retrieve(
            query=query,
            hotel_id=hotel_id,
            brain_id=brain_id,
        )

        return self.repository.get_by_ids(
            ids
        )