from __future__ import annotations
from lxml import etree
from docx import Document
from docx.opc.packuri import PackURI
from docx.opc.part import Part

CUSTOM_PROPS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
CUSTOM_PROPS_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
)
CUSTOM_PROPS_PARTNAME = "/docProps/custom.xml"
CUSTOM_PROPS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.custom-properties+xml"
)


def _get_custom_props_part(doc: Document) -> Part | None:
    """Return the docProps/custom.xml package part, or None if not present."""
    try:
        return doc.part.package.part_related_by(CUSTOM_PROPS_REL)
    except KeyError:
        return None


def _create_custom_props_part(doc: Document) -> Part:
    """Create an empty docProps/custom.xml part and relate it to the package."""
    root = etree.Element(
        f"{{{CUSTOM_PROPS_NS}}}Properties", nsmap={None: CUSTOM_PROPS_NS, "vt": VT_NS}
    )
    blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    package = doc.part.package
    part = Part(PackURI(CUSTOM_PROPS_PARTNAME), CUSTOM_PROPS_CONTENT_TYPE, blob, package)
    package.relate_to(part, CUSTOM_PROPS_REL)
    return part


def _get_custom_props_element(doc: Document) -> etree._Element | None:
    """Return the root element of docProps/custom.xml, or None if not present."""
    part = _get_custom_props_part(doc)
    if part is None:
        return None
    return etree.fromstring(part.blob)


def _set_custom_props_element(doc: Document, root: etree._Element) -> None:
    """Serialize and write the custom properties XML back to the package.

    Creates the docProps/custom.xml part if it does not already exist.
    """
    part = _get_custom_props_part(doc) or _create_custom_props_part(doc)
    part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def get_custom_property(doc: Document, name: str) -> str | None:
    """Read a custom document property by name."""
    root = _get_custom_props_element(doc)
    if root is None:
        return None
    for prop in root:
        if prop.get("name") == name:
            for child in prop:
                return child.text
    return None


def set_custom_property(doc: Document, name: str, value: str) -> None:
    """Set a custom document property. Updates if exists, creates if not."""
    root = _get_custom_props_element(doc)
    if root is None:
        # No custom-properties part yet; start from an empty Properties root.
        root = etree.Element(
            f"{{{CUSTOM_PROPS_NS}}}Properties", nsmap={None: CUSTOM_PROPS_NS, "vt": VT_NS}
        )

    # Look for existing property
    for prop in root:
        if prop.get("name") == name:
            for child in prop:
                child.text = value
            _set_custom_props_element(doc, root)
            return

    # Add new property
    fmtid = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"
    props = list(root)
    pid = max((int(p.get("pid", 1)) for p in props), default=1) + 1
    new_prop = etree.SubElement(root, f"{{{CUSTOM_PROPS_NS}}}property")
    new_prop.set("fmtid", fmtid)
    new_prop.set("pid", str(pid))
    new_prop.set("name", name)
    vt_lpwstr = etree.SubElement(new_prop, f"{{{VT_NS}}}lpwstr")
    vt_lpwstr.text = value
    _set_custom_props_element(doc, root)


def update_study_properties(
    doc: Document,
    study_uid: str,
    study_id: str,
    version: str | None,
    version_status: str | None,
    synced_at: str,
) -> None:
    """Update the five standard OSB custom document properties."""
    set_custom_property(doc, "StudyUID", study_uid)
    set_custom_property(doc, "StudyId", study_id)
    set_custom_property(doc, "StudyVersion", version or "LATEST")
    set_custom_property(doc, "StudyVersionStatus", version_status or "DRAFT")
    set_custom_property(doc, "OSBSyncedAt", synced_at)
