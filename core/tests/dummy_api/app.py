from __future__ import annotations
import json
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, Response

FIXTURES = Path(__file__).parent.parent / "fixtures"

app = FastAPI(title="OSB Dummy API", description="Test fixture server for elobs-word-updater")


def _load_json(name: str) -> dict:
    p = FIXTURES / name
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Fixture {name} not found")
    return json.loads(p.read_text(encoding="utf-8"))


def _load_bytes(name: str) -> bytes:
    p = FIXTURES / name
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Fixture {name} not found")
    return p.read_bytes()


def _version_suffix(version: str | None) -> str:
    return "_v1" if version == "1" else "_latest"


@app.get("/api/studies")
def get_studies(page_size: int = Query(default=0)):
    return JSONResponse(_load_json("studies.json"))


@app.get("/api/studies/{uid}")
def get_study(uid: str, study_value_version: str | None = Query(default=None)):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    return JSONResponse(_load_json(f"study_000001{suffix}.json"))


@app.get("/api/studies/{uid}/protocol-title")
def get_protocol_title(uid: str, study_value_version: str | None = Query(default=None)):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    return JSONResponse(_load_json(f"protocol_title{suffix}.json"))


@app.get("/api/studies/{uid}/study-criteria")
def get_study_criteria(uid: str, study_value_version: str | None = Query(default=None)):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    return JSONResponse(_load_json(f"study_criteria{suffix}.json"))


@app.get("/api/studies/{uid}/snapshot-history")
def get_snapshot_history(uid: str):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    return JSONResponse(_load_json("snapshot_history.json"))


@app.get("/api/studies/{uid}/study-objectives.docx")
def get_objectives_docx(uid: str, study_value_version: str | None = Query(default=None)):
    if uid == "Study_000003":
        data = _load_bytes("objectives_endpoints_study_000003.docx")
        return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    fname = f"objectives_endpoints{suffix}.docx" if suffix == "_v1" else "objectives_endpoints.docx"
    data = _load_bytes(fname)
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/api/studies/{uid}/flowchart.docx")
def get_flowchart_docx(uid: str, study_value_version: str | None = Query(default=None)):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    fname = f"flowchart{suffix}.docx" if suffix == "_v1" else "flowchart.docx"
    data = _load_bytes(fname)
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/api/studies/{uid}/design.svg")
def get_design_svg(uid: str, study_value_version: str | None = Query(default=None)):
    if uid != "Study_000001":
        raise HTTPException(status_code=404, detail="Study not found")
    suffix = _version_suffix(study_value_version)
    fname = f"design{suffix}.svg" if suffix == "_v1" else "design.svg"
    data = _load_bytes(fname)
    return Response(content=data, media_type="image/svg+xml")
