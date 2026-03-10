from __future__ import annotations
import httpx
from .base import AuthClient


class OAuthClient(AuthClient):
    """
    OAuth 2.0 authentication client (not yet implemented).

    Planned: generic OAuth 2.0 via MSAL, supporting Azure AD, Keycloak, etc.
    """

    def __init__(self, base_url: str, client_id: str, authority: str, scopes: list[str]) -> None:
        self._base_url = base_url
        self._client_id = client_id
        self._authority = authority
        self._scopes = scopes

    async def get_client(self) -> httpx.AsyncClient:
        raise NotImplementedError(
            "OAuth authentication is not yet implemented. "
            "Use auth.type=none in your config for now."
        )
