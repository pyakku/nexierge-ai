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
    ) -> list[str]:

        embedding = embed_query(
            query
        )

        brain_filter = BRAIN_FILTERS[
            brain_id
        ]

        results = self.index.query(
            vector=embedding,
            top_k=TOP_K,
            include_metadata=False,
            filter={
                "hotel_id": hotel_id,
                brain_filter: True,
                "status": "deployed",
            },
        )

        matches = results["matches"]

        if not matches:
            return []

        best_score = matches[0]["score"]

        threshold = best_score * SCORE_RATIO

        print("\n=== RETRIEVAL RESULTS ===")
        print(f"Best Score: {best_score}")
        print(f"Threshold: {threshold}")

        filtered_ids = []

        for match in matches:

            print(
                match["id"],
                match["score"]
            )

            if match["score"] >= threshold:
                filtered_ids.append(
                    match["id"]
                )

        print(
            f"\nKept {len(filtered_ids)} chunks"
        )

        return filtered_ids[
            :MAX_CONTEXT_ITEMS
        ]