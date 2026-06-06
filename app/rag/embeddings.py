from app.core.openai_client import client


def embed_query(
    query: str,
) -> list[float]:

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1024,
    )

    return response.data[0].embedding