#!/usr/bin/env python3
"""
Fetch fresh fixture data from a running OpenStudyBuilder API.

Usage:
    python scripts/fetch_fixtures.py --api http://localhost:5005/api --study Study_000001
"""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
import httpx

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"


async def fetch_all(api_url: str, study_uid: str) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    base = api_url.rstrip("/")

    async with httpx.AsyncClient(base_url=base, timeout=60) as client:
        async def get_json(path: str, params: dict | None = None) -> dict:
            r = await client.get(path, params=params or {})
            r.raise_for_status()
            return r.json()

        async def get_bytes(path: str, params: dict | None = None) -> bytes:
            r = await client.get(path, params=params or {})
            r.raise_for_status()
            return r.content

        print("Fetching studies list...")
        studies = await get_json("/studies", {"page_size": 10})
        (FIXTURES / "studies.json").write_text(json.dumps(studies, indent=2, ensure_ascii=False))

        print("Fetching snapshot history...")
        history = await get_json(f"/studies/{study_uid}/snapshot-history")
        (FIXTURES / "snapshot_history.json").write_text(json.dumps(history, indent=2, ensure_ascii=False))

        for version, suffix in [(None, "_latest"), ("1", "_v1")]:
            params = {"study_value_version": version} if version else {}
            label = f"v{version}" if version else "LATEST"
            print(f"Fetching study detail ({label})...")
            data = await get_json(f"/studies/{study_uid}", params)
            (FIXTURES / f"study_000001{suffix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

            print(f"Fetching protocol-title ({label})...")
            data = await get_json(f"/studies/{study_uid}/protocol-title", params)
            (FIXTURES / f"protocol_title{suffix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

            print(f"Fetching study-criteria ({label})...")
            data = await get_json(f"/studies/{study_uid}/study-criteria", params)
            (FIXTURES / f"study_criteria{suffix}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

            docx_suffix = "_v1" if version == "1" else ""
            print(f"Fetching objectives.docx ({label})...")
            data = await get_bytes(f"/studies/{study_uid}/study-objectives.docx", params)
            (FIXTURES / f"objectives_endpoints{docx_suffix}.docx").write_bytes(data)

            print(f"Fetching flowchart.docx ({label})...")
            data = await get_bytes(f"/studies/{study_uid}/flowchart.docx", params)
            (FIXTURES / f"flowchart{docx_suffix}.docx").write_bytes(data)

            print(f"Fetching design.svg ({label})...")
            data = await get_bytes(f"/studies/{study_uid}/design.svg", params)
            (FIXTURES / f"design{docx_suffix}.svg").write_bytes(data)

        print(f"\nAll fixtures written to {FIXTURES}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:5005/api")
    parser.add_argument("--study", default="Study_000001")
    args = parser.parse_args()
    asyncio.run(fetch_all(args.api, args.study))
