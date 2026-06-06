from time import perf_counter

from app.models.brain import Brain
from app.rag.knowledge_repository import (
    KnowledgeRepository,
)
from app.rag.retriever import Retriever


class KnowledgeService:

    def __init__(self):
        self.retriever = Retriever()
        self.repository = (
            KnowledgeRepository()
        )

    def retrieve(
        self,
        query: str,
        hotel_id: str,
        brain_id: Brain,
        sandbox: bool = False,
    ):

        retrieval_start = perf_counter()

        ids = self.retriever.retrieve(
            query=query,
            hotel_id=hotel_id,
            brain_id=brain_id,
            sandbox=sandbox,
        )

        retrieval_end = perf_counter()

        print(
            f"ID Retrieval: {(retrieval_end - retrieval_start) * 1000:.0f}ms"
        )

        if not ids:
            return []

        xano_start = perf_counter()

        knowledge = self.repository.get_by_ids(
            ids
        )

        xano_end = perf_counter()

        print(
            f"Xano: {(xano_end - xano_start) * 1000:.0f}ms"
        )

        print(
            f"Knowledge Total: {(xano_end - retrieval_start) * 1000:.0f}ms"
        )

        return knowledge