import logging
from time import perf_counter

from app.models.brain import Brain
from app.rag.knowledge_repository import KnowledgeRepository
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)


class KnowledgeService:

    def __init__(self):
        self.retriever = Retriever()
        self.repository = KnowledgeRepository()

    def retrieve(
        self,
        query: str,
        hotel_id: str,
        brain_id: Brain,
        sandbox: bool = False,
    ):

        start = perf_counter()

        ids = self.retriever.retrieve(
            query=query,
            hotel_id=hotel_id,
            brain_id=brain_id,
            sandbox=sandbox,
        )

        retrieval_ms = int((perf_counter() - start) * 1000)

        if not ids:
            return []

        xano_start = perf_counter()
        knowledge = self.repository.get_by_ids(ids)
        xano_ms = int((perf_counter() - xano_start) * 1000)

        logger.debug(
            "knowledge.complete",
            extra={
                "retrieval_ms": retrieval_ms,
                "xano_ms": xano_ms,
                "total_ms": retrieval_ms + xano_ms,
                "ids_found": len(ids),
                "items_returned": len(knowledge),
            },
        )

        return knowledge
