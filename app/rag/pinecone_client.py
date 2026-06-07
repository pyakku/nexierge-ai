import os

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()


def get_index(
    name: str | None = None,
):
    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY")
    )

    return pc.Index(
        name or os.getenv("PINECONE_INDEX")
    )
