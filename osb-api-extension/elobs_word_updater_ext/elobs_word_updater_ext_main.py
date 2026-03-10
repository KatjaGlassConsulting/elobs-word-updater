from __future__ import annotations
import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import Response
from docx import Document
from elobs_word_updater.document.content_controls import get_content_control_tags
from elobs_word_updater.updater import update_document
try:
    from .osb_direct_client import OsbDirectClient  # package import (tests)
except ImportError:
    from osb_direct_client import OsbDirectClient  # top-level import (OSB extensions loader)

log = logging.getLogger(__name__)

router = APIRouter(
    tags=["ElObsWordUpdater"],
)


@router.post(
    "/generate",
    summary="Generate a populated Word document",
    response_description="Updated .docx file",
)
async def generate_document(
    template: UploadFile = File(..., description="Word template (.docx) with SB_* content controls"),
    study_uid: str = Form(..., description="OpenStudyBuilder study UID"),
    version: str | None = Form(None, description="Study version number. Omit for latest."),
    tags: list[str] | None = Form(None, description="SB_* tags to update. Omit to update all."),
):
    """
    Accept a Word template and study parameters, populate all SB_* content controls
    with data from the OpenStudyBuilder API, and return the updated document.
    """
    template_bytes = await template.read()

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, "template.docx")
        output_path = os.path.join(tmp, "output.docx")

        with open(input_path, "wb") as f:
            f.write(template_bytes)

        client = OsbDirectClient()

        _doc = Document(input_path)
        log.info("Tags found in template: %s", get_content_control_tags(_doc))

        version = version or None  # normalize empty string → None (latest)
        filtered_tags = [t for t in tags if t] if tags else None
        filtered_tags = filtered_tags or None  # empty list → update all
        result = await update_document(
            doc_path=input_path,
            output_path=output_path,
            study_uid=study_uid,
            version=version,
            api_client=client,
            tags=filtered_tags,  # None means update all tags
        )
        log.info("Updated  : %s", result.updated)
        log.info("Skipped  : %s", result.skipped)
        log.info("Missing  : %s", result.missing)
        log.info("API errors: %s", result.api_errors)

        with open(output_path, "rb") as f:
            result_bytes = f.read()

    filename = f"{study_uid}_v{version or 'latest'}.docx"
    return Response(
        content=result_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
