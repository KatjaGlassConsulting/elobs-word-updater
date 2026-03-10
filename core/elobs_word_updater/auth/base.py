from __future__ import annotations
from abc import ABC, abstractmethod
import httpx


class AuthClient(ABC):
    """Base class for authentication strategies."""

    @abstractmethod
    async def get_client(self) -> httpx.AsyncClient:
        """Return an authenticated httpx.AsyncClient."""
        ...
