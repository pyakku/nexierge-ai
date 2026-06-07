import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

_MAX_RETRIES = 3
_RETRY_STATUSES = {500, 502, 503, 504}


class XanoClient:

    def __init__(self):
        self.base_url = os.getenv("XANO_BASE_URL")
        self.headers = {
            "auth": os.getenv("XANO_PYTHON_KEY")
        }
        self._client = httpx.Client(timeout=30)

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ):
        url = f"{self.base_url}/{endpoint}"
        last_exc = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client.request(
                    method,
                    url,
                    headers=self.headers,
                    **kwargs,
                )
                if (
                    response.status_code in _RETRY_STATUSES
                    and attempt < _MAX_RETRIES - 1
                ):
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        raise last_exc

    def post(self, endpoint: str, data: dict):
        return self._request("POST", endpoint, json=data)

    def get(self, endpoint: str, params: dict):
        return self._request("GET", endpoint, params=params)
