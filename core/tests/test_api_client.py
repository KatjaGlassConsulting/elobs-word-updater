from __future__ import annotations
import pytest
import httpx
from elobs_word_updater.auth.no_auth import NoAuthClient
from elobs_word_updater.api.client import StudyApiClient
from tests.conftest import DUMMY_API_URL


@pytest.fixture
def client():
    auth = NoAuthClient(DUMMY_API_URL)
    return StudyApiClient(auth)


@pytest.mark.asyncio
async def test_get_studies(client):
    """Fetches the studies list and verifies Study_000001 is present."""
    studies = await client.get_studies()
    assert isinstance(studies, list)
    assert any(s["uid"] == "Study_000001" for s in studies)


@pytest.mark.asyncio
async def test_get_study_latest(client):
    """Fetches the latest version of Study_000001 and checks identification metadata."""
    study = await client.get_study("Study_000001")
    meta = study["current_metadata"]["identification_metadata"]
    assert "study_id" in meta


@pytest.mark.asyncio
async def test_get_study_version1(client):
    """Fetches version 1 of Study_000001 and verifies the title has no '(new)' suffix."""
    study = await client.get_study("Study_000001", version="1")
    desc = study["current_metadata"]["study_description"]
    # v1 title should NOT have "(new)" suffix
    assert "(new)" not in desc["study_title"]


@pytest.mark.asyncio
async def test_get_protocol_title_latest(client):
    """Latest protocol title contains the '(new)' suffix."""
    pt = await client.get_protocol_title("Study_000001")
    assert "(new)" in pt["study_title"]


@pytest.mark.asyncio
async def test_get_protocol_title_v1(client):
    """Version 1 protocol title does not contain the '(new)' suffix."""
    pt = await client.get_protocol_title("Study_000001", version="1")
    assert "(new)" not in pt["study_title"]


@pytest.mark.asyncio
async def test_get_study_criteria(client):
    """Study criteria list includes an Exclusion Criteria entry."""
    items = await client.get_study_criteria("Study_000001")
    assert isinstance(items, list)
    types = {item["criteria_type"]["term_name"] for item in items}
    assert "Exclusion Criteria" in types


@pytest.mark.asyncio
async def test_get_objectives_docx(client):
    """Objectives DOCX response is a valid ZIP/DOCX byte stream."""
    data = await client.get_objectives_docx("Study_000001")
    assert data[:4] == b"PK\x03\x04"  # DOCX is a ZIP


@pytest.mark.asyncio
async def test_get_flowchart_docx(client):
    """Flowchart DOCX response is a valid ZIP/DOCX byte stream."""
    data = await client.get_flowchart_docx("Study_000001")
    assert data[:4] == b"PK\x03\x04"


@pytest.mark.asyncio
async def test_get_design_svg(client):
    """Design SVG response contains valid SVG markup."""
    data = await client.get_design_svg("Study_000001")
    assert b"<svg" in data or b"<?xml" in data


@pytest.mark.asyncio
async def test_get_snapshot_history(client):
    """Snapshot history returns a non-empty list."""
    items = await client.get_snapshot_history("Study_000001")
    assert isinstance(items, list)
    assert len(items) > 0


@pytest.mark.asyncio
async def test_get_study_unknown_raises(client):
    """Unknown study UID returns 404, which raises HTTPStatusError."""
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_study("Unknown_Study_XYZ")


@pytest.mark.asyncio
async def test_get_protocol_title_unknown_raises(client):
    """Unknown study UID raises HTTPStatusError for the protocol title endpoint."""
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_protocol_title("Unknown_Study_XYZ")


@pytest.mark.asyncio
async def test_get_study_criteria_unknown_raises(client):
    """Unknown study UID raises HTTPStatusError for the study criteria endpoint."""
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_study_criteria("Unknown_Study_XYZ")


@pytest.mark.asyncio
async def test_get_study_criteria_v1(client):
    """Fetches version 1 study criteria and verifies the result is a non-empty list."""
    items = await client.get_study_criteria("Study_000001", version="1")
    assert isinstance(items, list)
    assert len(items) > 0


@pytest.mark.asyncio
async def test_get_studies_returns_list_of_dicts(client):
    """Each item in the studies list is a dict."""
    studies = await client.get_studies()
    assert all(isinstance(s, dict) for s in studies)


@pytest.mark.asyncio
async def test_get_design_svg_v1(client):
    """Version 1 design SVG response contains valid SVG markup."""
    data = await client.get_design_svg("Study_000001", version="1")
    assert b"<svg" in data or b"<?xml" in data


@pytest.mark.asyncio
async def test_version_params_none_fetches_latest(client):
    """Passing version=None should still return data (latest)."""
    study = await client.get_study("Study_000001", version=None)
    assert study is not None


@pytest.mark.asyncio
async def test_get_snapshot_history_unknown_raises(client):
    """Unknown study UID raises HTTPStatusError for the snapshot history endpoint."""
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_snapshot_history("Unknown_Study_XYZ")
