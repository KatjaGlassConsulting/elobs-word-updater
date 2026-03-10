from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import yaml


@dataclass
class OAuthConfig:
    client_id: str
    authority: str
    scopes: list[str] = field(default_factory=list)


@dataclass
class AuthConfig:
    type: Literal["none", "oauth"] = "none"
    oauth: OAuthConfig | None = None


@dataclass
class ApiConfig:
    url: str = "http://localhost:5005/api"
    auth: AuthConfig = field(default_factory=AuthConfig)


@dataclass
class Config:
    api: ApiConfig = field(default_factory=ApiConfig)


def load_config(path: Path | str | None = None) -> Config:
    if path is None:
        candidates = [Path("config.yaml"), Path("config.yml")]
        path = next((p for p in candidates if p.exists()), None)
    if path is None or not Path(path).exists():
        return Config()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    api_data = data.get("api", {})
    auth_data = api_data.get("auth", {})
    oauth_data = auth_data.get("oauth")
    oauth = OAuthConfig(**oauth_data) if oauth_data else None
    auth = AuthConfig(type=auth_data.get("type", "none"), oauth=oauth)
    api = ApiConfig(url=api_data.get("url", "http://localhost:5005/api"), auth=auth)
    return Config(api=api)
