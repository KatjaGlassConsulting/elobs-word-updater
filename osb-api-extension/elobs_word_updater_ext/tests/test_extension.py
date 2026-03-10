from __future__ import annotations
import io
import pytest
from docx import Document
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

# The extensions app is loaded from OSB's extensions_api.py once this
# extension folder is placed inside clinical-mdr-api/extensions/.
# For isolated unit testing we build a minimal app here.
from fastapi import FastAPI
from elobs_word_updater_ext.elobs_word_updater_ext_main import router

app = FastAPI()
app.include_router(router, prefix="/elobs-word-updater")


@pytest.fixture(scope="module")
def api_client():
    """Create a FastAPI test client for the extension."""
    yield TestClient(app)


def _make_template_bytes() -> bytes:
    """Create a minimal .docx with one SB_ProtocolTitle content control."""
    from lxml import etree
    W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    doc = Document()
    xml = f'<w:sdt xmlns:w="{W_NS}"><w:sdtPr><w:tag w:val="SB_ProtocolTitle"/></w:sdtPr><w:sdtContent><w:p><w:r><w:t>PLACEHOLDER</w:t></w:r></w:p></w:sdtContent></w:sdt>'
    doc.element.body.append(etree.fromstring(xml))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_generate_returns_docx(api_client):
    """A valid request returns a .docx file (ZIP magic bytes)."""
    mock_result = MagicMock(updated=["SB_ProtocolTitle"], skipped=[], missing=[], api_errors={})

    with patch(
        "elobs_word_updater_ext.elobs_word_updater_ext_main.update_document",
        new=AsyncMock(side_effect=_write_dummy_output),
    ):
        response = api_client.post(
            "/elobs-word-updater/generate",
            data={"study_uid": "Study_000001"},
            files={"template": ("template.docx", _make_template_bytes(), "application/octet-stream")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert response.content[:4] == b"PK\x03\x04"


def test_generate_missing_study_uid(api_client):
    """Omitting study_uid returns a validation error."""
    response = api_client.post(
        "/elobs-word-updater/generate",
        data={},
        files={"template": ("template.docx", _make_template_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 422


def test_generate_missing_template(api_client):
    """Omitting the template file returns a validation error."""
    response = api_client.post(
        "/elobs-word-updater/generate",
        data={"study_uid": "Study_000001"},
    )
    assert response.status_code == 422


async def _write_dummy_output(**kwargs):
    """Side-effect helper: writes a valid empty .docx to output_path."""
    doc = Document()
    doc.save(kwargs["output_path"])
    return MagicMock(updated=[], skipped=[], missing=[], api_errors={})
