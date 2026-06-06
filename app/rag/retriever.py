from app.models.brain import Brain
from app.rag.embeddings import embed_query
from app.rag.pinecone_client import get_index


BRAIN_FILTERS = {
    Brain.GENERAL: "GENERAL",
    Brain.LEAD_AND_UNKNOWN: "PRE_STAY_SALES",
    Brain.GUEST_PRE_ARRIVAL: "PRE_STAY_IDENTIFIED",
    Brain.GUEST_IN_STAY: "IN_STAY",
    Brain.GUEST_POST_STAY: "POST_STAY",
    Brain.PAST_GUEST: "RETURNING_LEAD",
}


class Retriever:

    def __init__(self):
        self.index = get_index()

    def retrieve(
        self,
        query: str,
        hotel_id: str,
        brain_id: Brain,
        top_k: int = 5,
    ) -> list[str]:

        embedding = embed_query(
            query
        )

        brain_filter = BRAIN_FILTERS[
            brain_id
        ]

        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=False,
            filter={
                "hotel_id": hotel_id,
                brain_filter: True,
                "status": "deployed",
            },
        )

        return [
            match["id"]
            for match in results["matches"]
        ]