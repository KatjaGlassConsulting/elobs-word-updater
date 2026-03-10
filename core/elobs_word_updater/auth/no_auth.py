from __future__ import annotations
import httpx
from .base import AuthClient


class NoAuthClient(AuthClient):
    """Plain HTTP client with no authentication."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, timeout=60.0)
