from __future__ import annotations
from ..config import AuthConfig
from .base import AuthClient
from .no_auth import NoAuthClient
from .oauth import OAuthClient


def create_auth_client(base_url: str, auth_config: AuthConfig) -> AuthClient:
    if auth_config.type == "none":
        return NoAuthClient(base_url)
    if auth_config.type == "oauth":
        if auth_config.oauth is None:
            raise ValueError("OAuth config is required when auth.type=oauth")
        return OAuthClient(
            base_url=base_url,
            client_id=auth_config.oauth.client_id,
            authority=auth_config.oauth.authority,
            scopes=auth_config.oauth.scopes,
        )
    raise ValueError(f"Unknown auth type: {auth_config.type!r}")
