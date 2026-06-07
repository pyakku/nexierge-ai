import os
from time import perf_counter

from app.models.brain import Brain
from app.rag.embeddings import embed_query
from app.rag.pinecone_client import get_index
from app.rag.retriever import BRAIN_FILTERS
from app.rag.settings import (
    MAX_CONTEXT_ITEMS,
    SCORE_RATIO,
    TOP_K,
)


class MediaRetriever:

    def __init__(self):
        self.index = get_index(
            os.getenv("PINECONE_MEDIA_INDEX", "media")
        )

    def retrieve(
        self,
        query: str,
        hotel_id: str,
        brain_id: Brain,
        sandbox: bool = False,
    ) -> list[dict]:

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
            include_metadata=True,
            filter=filter,
        )

        pinecone_time = perf_counter()

        print(
            f"Media Embedding: {(embedding_time - start) * 1000:.0f}ms"
        )

        print(
            f"Media Pinecone: {(pinecone_time - embedding_time) * 1000:.0f}ms"
        )

        matches = results["matches"]

        if not matches:
            return []

        best_score = matches[0]["score"]
        threshold = best_score * SCORE_RATIO
        items = []

        for match in matches:

            if match["score"] < threshold:
                continue

            metadata = match.get(
                "metadata", {}
            )

            url = metadata.get("url")

            if not url:
                continue

            items.append(
                {
                    "url": url,
                    "desc": metadata.get(
                        "desc", ""
                    ),
                }
            )

        end = perf_counter()

        print(
            f"Media Total: {(end - start) * 1000:.0f}ms"
        )

        return items[:MAX_CONTEXT_ITEMS]
