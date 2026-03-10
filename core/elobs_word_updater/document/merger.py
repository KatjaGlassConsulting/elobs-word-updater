from __future__ import annotations
import io
from copy import deepcopy
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
from .content_controls import find_content_control

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _copy_relationships(target: Document, source: Document) -> dict[str, str]:
    """
    Copy all non-external relationships from source to target.
    Returns a mapping {old_rId: new_rId}.

    Parts that already exist in the target package (same partname) are reused
    rather than duplicated, preventing invalid ZIP entries in the output file.
    """
    existing = {p.partname: p for p in target.part.package.iter_parts()}
    rId_map: dict[str, str] = {}
    for rId, rel in source.part.rels.items():
        if not rel.is_external:
            try:
                src_part = rel.target_part
                dest_part = existing.get(src_part.partname, src_part)
                new_rId = target.part.relate_to(dest_part, rel.reltype)
                if src_part.partname not in existing:
                    existing[src_part.partname] = src_part
                rId_map[rId] = new_rId
            except Exception:
                pass
    return rId_map


def _remap_rids(element: etree._Element, rId_map: dict[str, str]) -> None:
    """Update all r:id / r:embed / r:link attributes using the rId mapping."""
    ns_r = R_NS
    attrs = [f"{{{ns_r}}}id", f"{{{ns_r}}}embed", f"{{{ns_r}}}link"]
    for elem in element.iter():
        for attr in attrs:
            old = elem.get(attr)
            if old and old in rId_map:
                elem.set(attr, rId_map[old])


def insert_docx_at_content_control(main_doc: Document, tag: str, docx_bytes: bytes) -> bool:
    """
    Insert the body content of a DOCX file into the content control identified
    by `tag`, replacing its existing content while keeping the control itself.

    Relationships (images, etc.) are copied from the sub-document to the main
    document so all embedded content remains intact.

    Returns True if the control was found and updated.
    """
    sdt = find_content_control(main_doc, tag)
    if sdt is None:
        return False

    sdt_content = sdt.find(_w("sdtContent"))
    if sdt_content is None:
        return False

    sub_doc = Document(io.BytesIO(docx_bytes))
    rId_map = _copy_relationships(main_doc, sub_doc)

    # Collect body elements, skipping the final sectPr
    elements = [
        deepcopy(child)
        for child in sub_doc.element.body
        if child.tag != _w("sectPr")
    ]

    for elem in elements:
        _remap_rids(elem, rId_map)

    for child in list(sdt_content):
        sdt_content.remove(child)

    # Wrap the inserted content with empty paragraphs so Word renders both the
    # opening and closing field markers outside the content (e.g. not inside
    # the first/last table row when the sub-document starts or ends with a table).
    sdt_content.append(etree.Element(_w("p")))

    for elem in elements:
        sdt_content.append(elem)

    sdt_content.append(etree.Element(_w("p")))

    return True
