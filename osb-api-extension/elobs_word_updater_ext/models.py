from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    study_uid: str = Field(..., description="OpenStudyBuilder study UID (e.g. Study_000001)")
    version: Optional[str] = Field(None, description="Study version number. Omit for latest.")
    tags: Optional[list[str]] = Field(None, description="SB_* tags to update. Omit to update all.")
