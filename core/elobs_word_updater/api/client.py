from __future__ import annotations
import io
from typing import Any
import httpx
from ..auth.base import AuthClient


class StudyApiClient:
    """Client for all OpenStudyBuilder API calls."""

    def __init__(self, auth_client: AuthClient) -> None:
        self._auth = auth_client

    def _version_params(self, version: str | None) -> dict[str, str]:
        if version:
            return {"study_value_version": version}
        return {}

    async def get_studies(self, page_size: int = 0) -> list[dict[str, Any]]:
        async with await self._auth.get_client() as client:
            r = await client.get("/studies", params={"page_size": page_size})
            r.raise_for_status()
            return r.json().get("items", [])

    async def get_study(self, uid: str, version: str | None = None) -> dict[str, Any]:
        async with await self._auth.get_client() as client:
            r = await client.get(f"/studies/{uid}", params=self._version_params(version))
            r.raise_for_status()
            return r.json()

    async def get_protocol_title(self, uid: str, version: str | None = None) -> dict[str, Any]:
        async with await self._auth.get_client() as client:
            r = await client.get(
                f"/studies/{uid}/protocol-title", params=self._version_params(version)
            )
            r.raise_for_status()
            return r.json()

    async def get_study_criteria(self, uid: str, version: str | None = None) -> list[dict[str, Any]]:
        async with await self._auth.get_client() as client:
            r = await client.get(
                f"/studies/{uid}/study-criteria", params=self._version_params(version)
            )
            r.raise_for_status()
            return r.json().get("items", [])

    async def get_objectives_docx(self, uid: str, version: str | None = None) -> bytes:
        async with await self._auth.get_client() as client:
            r = await client.get(
                f"/studies/{uid}/study-objectives.docx", params=self._version_params(version)
            )
            r.raise_for_status()
            return r.content

    async def get_flowchart_docx(self, uid: str, version: str | None = None) -> bytes:
        async with await self._auth.get_client() as client:
            r = await client.get(
                f"/studies/{uid}/flowchart.docx", params=self._version_params(version)
            )
            r.raise_for_status()
            return r.content

    async def get_design_svg(self, uid: str, version: str | None = None) -> bytes:
        async with await self._auth.get_client() as client:
            r = await client.get(
                f"/studies/{uid}/design.svg", params=self._version_params(version)
            )
            r.raise_for_status()
            return r.content

    async def get_snapshot_history(self, uid: str) -> list[dict[str, Any]]:
        async with await self._auth.get_client() as client:
            r = await client.get(f"/studies/{uid}/snapshot-history")
            r.raise_for_status()
            return r.json().get("items", [])
