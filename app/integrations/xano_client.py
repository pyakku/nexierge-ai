import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class XanoClient:

    def __init__(self):
        self.base_url = os.getenv(
            "XANO_BASE_URL"
        )

        self.headers = {
            "auth": os.getenv(
                "XANO_PYTHON_KEY"
            )
        }

    def post(
        self,
        endpoint: str,
        data: dict,
    ):
        response = httpx.post(
            f"{self.base_url}/{endpoint}",
            json=data,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()