from time import perf_counter

from app.models.brain import Brain
from app.rag.embeddings import embed_query
from app.rag.pinecone_client import get_index
from app.rag.settings import (
    TOP_K,
    MAX_CONTEXT_ITEMS,
    SCORE_RATIO,
)


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
        sandbox: bool = False,
    ) -> list[str]:

        start = perf_counter()

        embedding = embed_query(
            query
        )

        embedding_time = perf_counter()

        brain_filter = BRAIN_FILTERS[
            brain_id
        ]

        status_filter = (
            {
                "$or": [
                    {
                        "status": "active",
                    },
                    {
                        "status": "deployed",
                    },
                ]
            }
            if sandbox
            else {
                "status": "deployed",
            }
        )

        filter = {
            "$and": [
                {
                    "$or": [
                        {
                            "GENERAL": True,
                        },
                        {
                            brain_filter: True,
                        },
                    ]
                },
                {
                    "hotel_id": hotel_id,
                },
                status_filter,
            ]
        }

        results = self.index.query(
            vector=embedding,
            top_k=TOP_K,
            include_metadata=False,
            filter=filter,
        )

        pinecone_time = perf_counter()

        print(
            f"Embedding: {(embedding_time - start) * 1000:.0f}ms"
        )

        print(
            f"Pinecone: {(pinecone_time - embedding_time) * 1000:.0f}ms"
        )

        matches = results["matches"]

        if not matches:
            return []

        best_score = matches[0]["score"]

        threshold = best_score * SCORE_RATIO

        filtered_ids = []

        for match in matches:

            if match["score"] >= threshold:
                filtered_ids.append(
                    match["id"]
                )

        end = perf_counter()

        print(
            f"Retriever Total: {(end - start) * 1000:.0f}ms"
        )

        return filtered_ids[
            :MAX_CONTEXT_ITEMS
        ]