from __future__ import annotations
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
import click
import httpx
from docx import Document
from .api.client import StudyApiClient
from .document.content_controls import (
    set_content_control_text,
    set_content_control_lines,
    get_content_control_tags,
    clear_content_control,
)
from .document.merger import insert_docx_at_content_control
from .document.svg_embedder import embed_svg_at_content_control
from .document.properties import update_study_properties


# All supported SB_ tags
TEXT_TAGS: set[str] = {
    "SB_ProtocolTitle", "SB_Acronym", "SB_ProtocolTitleShort", "SB_Substance",
    "SB_StudyID", "SB_UniversalTrialNumber", "SB_EUTrialNumber", "SB_EudraCTNumber",
    "SB_INDNumber", "SB_CIVID_SIN", "SB_NCT", "SB_jRCT", "SB_NMPA",
    "SB_EUDAMED", "SB_IDE", "SB_StudyPhase",
}
CRITERIA_TAGS: set[str] = {"SB_InclusionCriteria", "SB_ExclusionCriteria"}
DOCX_TAGS: set[str] = {"SB_Flowchart", "SB_SoA", "SB_ObjectivesEndpoints"}
SVG_TAGS: set[str] = {"SB_StudydesignGraphic"}


@dataclass
class UpdateResult:
    updated: list[str]
    skipped: list[str]    # tag present in doc but no data from API
    missing: list[str]    # tag not found in document
    api_errors: list[str] = field(default_factory=list)  # endpoints that failed


async def update_document(
    doc_path: str,
    output_path: str,
    study_uid: str,
    version: str | None,
    api_client: StudyApiClient,
    tags: list[str] | None = None,
) -> UpdateResult:
    """
    Main entry point: load the template, fetch API data, update content controls,
    write to output_path.

    If `tags` is None, all SB_* tags found in the document are updated.
    """
    doc = Document(doc_path)
    doc_tags = set(get_content_control_tags(doc))

    if tags is not None:
        requested = set(tags)
    else:
        requested = doc_tags

    result = UpdateResult(updated=[], skipped=[], missing=[])

    # --- Fetch data from API (only what we need) ---
    needs_study = bool(requested & (TEXT_TAGS | CRITERIA_TAGS))
    needs_protocol_title = bool(requested & TEXT_TAGS)
    needs_criteria = bool(requested & CRITERIA_TAGS)
    needs_objectives = "SB_ObjectivesEndpoints" in requested
    needs_flowchart = bool(requested & {"SB_Flowchart", "SB_SoA"})
    needs_svg = "SB_StudydesignGraphic" in requested

    async def _fetch(coro, label, fallback):
        try:
            return await coro
        except Exception as exc:
            msg = str(exc).splitlines()[0]
            click.echo(f"Warning : {label} failed — {msg}", err=True)
            result.api_errors.append(label)
            return fallback

    study = await _fetch(api_client.get_study(study_uid, version), "study", {}) if needs_study else {}
    protocol_title = await _fetch(api_client.get_protocol_title(study_uid, version), "protocol-title", {}) if needs_protocol_title else {}
    criteria_items = await _fetch(api_client.get_study_criteria(study_uid, version), "study-criteria", []) if needs_criteria else []
    objectives_bytes = await _fetch(api_client.get_objectives_docx(study_uid, version), "study-objectives.docx", None) if needs_objectives else None
    flowchart_bytes = await _fetch(api_client.get_flowchart_docx(study_uid, version), "flowchart.docx", None) if needs_flowchart else None
    svg_bytes = await _fetch(api_client.get_design_svg(study_uid, version), "design.svg", None) if needs_svg else None

    reg = (study.get("current_metadata") or {}).get("identification_metadata") or {}
    registry = reg.get("registry_identifiers") or {}
    study_desc = (study.get("current_metadata") or {}).get("study_description") or {}

    def _text(tag: str, value: str | None) -> None:
        if tag not in requested:
            return
        if tag not in doc_tags:
            result.missing.append(tag)
            return
        if value is None:
            clear_content_control(doc, tag)
            result.skipped.append(tag)
            return
        set_content_control_text(doc, tag, value)
        result.updated.append(tag)

    def _lines(tag: str, lines: list[str]) -> None:
        if tag not in requested:
            return
        if tag not in doc_tags:
            result.missing.append(tag)
            return
        if not lines:
            clear_content_control(doc, tag)
            result.skipped.append(tag)
            return
        set_content_control_lines(doc, tag, lines)
        result.updated.append(tag)

    def _docx(tag: str, data: bytes | None) -> None:
        if tag not in requested:
            return
        if tag not in doc_tags:
            result.missing.append(tag)
            return
        if data is None:
            clear_content_control(doc, tag)
            result.skipped.append(tag)
            return
        insert_docx_at_content_control(doc, tag, data)
        result.updated.append(tag)

    def _svg(tag: str, data: bytes | None) -> None:
        if tag not in requested:
            return
        if tag not in doc_tags:
            result.missing.append(tag)
            return
        if data is None:
            clear_content_control(doc, tag)
            result.skipped.append(tag)
            return
        embed_svg_at_content_control(doc, tag, data)
        result.updated.append(tag)

    # --- Text fields ---
    _text("SB_ProtocolTitle", protocol_title.get("study_title"))
    _text("SB_ProtocolTitleShort", protocol_title.get("study_short_title"))
    _text("SB_Substance", protocol_title.get("substance_name"))
    _text("SB_EudraCTNumber", protocol_title.get("eudract_id"))
    _text("SB_INDNumber", protocol_title.get("ind_number"))
    _text("SB_UniversalTrialNumber", protocol_title.get("universal_trial_number_utn"))
    phase = (protocol_title.get("trial_phase_code") or {}).get("name")
    _text("SB_StudyPhase", phase)
    _text("SB_Acronym", reg.get("study_acronym"))
    _text("SB_StudyID", reg.get("study_id"))
    _text("SB_EUTrialNumber", registry.get("eu_trial_number"))
    _text("SB_CIVID_SIN", registry.get("civ_id_sin_number"))
    _text("SB_NCT", registry.get("ct_gov_id"))
    _text("SB_jRCT", registry.get("japanese_trial_registry_number_jrct"))
    _text("SB_NMPA", registry.get("national_medical_products_administration_nmpa_number"))
    _text("SB_EUDAMED", registry.get("eudamed_srn_number"))
    _text("SB_IDE", registry.get("investigational_device_exemption_ide_number"))

    # --- Criteria ---
    inclusion = [
        item["criteria"]["name_plain"]
        for item in criteria_items
        if item.get("criteria_type", {}).get("term_name") == "Inclusion Criteria"
        and item.get("criteria", {}).get("name_plain")
    ]
    exclusion = [
        item["criteria"]["name_plain"]
        for item in criteria_items
        if item.get("criteria_type", {}).get("term_name") == "Exclusion Criteria"
        and item.get("criteria", {}).get("name_plain")
    ]
    _lines("SB_InclusionCriteria", inclusion)
    _lines("SB_ExclusionCriteria", exclusion)

    # --- DOCX inserts ---
    _docx("SB_ObjectivesEndpoints", objectives_bytes)
    _docx("SB_Flowchart", flowchart_bytes)
    _docx("SB_SoA", flowchart_bytes)

    # --- SVG ---
    _svg("SB_StudydesignGraphic", svg_bytes)

    # --- Document properties ---
    study_id = reg.get("study_id", study_uid)
    version_status = (
        (study.get("current_metadata") or {})
        .get("version_metadata") or {}
    ).get("study_status", "DRAFT")
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    update_study_properties(doc, study_uid, study_id, version, version_status, synced_at)

    doc.save(output_path)
    return result
