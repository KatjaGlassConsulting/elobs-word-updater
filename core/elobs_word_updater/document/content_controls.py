from __future__ import annotations
from lxml import etree
from docx import Document
from docx.oxml.ns import qn

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def find_content_control(doc: Document, tag: str) -> etree._Element | None:
    """Find the first <w:sdt> element whose <w:tag w:val> matches `tag`."""
    for sdt in doc.element.body.iter(_w("sdt")):
        sdt_pr = sdt.find(_w("sdtPr"))
        if sdt_pr is None:
            continue
        tag_elem = sdt_pr.find(_w("tag"))
        if tag_elem is not None and tag_elem.get(_w("val")) == tag:
            return sdt
    return None


def set_content_control_text(doc: Document, tag: str, text: str) -> bool:
    """
    Replace the text content of a content control identified by tag.
    Returns True if the control was found and updated.
    """
    sdt = find_content_control(doc, tag)
    if sdt is None:
        return False
    content = sdt.find(_w("sdtContent"))
    if content is None:
        return False

    # Clear existing content
    for child in list(content):
        content.remove(child)

    # Build a plain paragraph with one run
    p = etree.SubElement(content, _w("p"))
    r = etree.SubElement(p, _w("r"))
    t = etree.SubElement(r, _w("t"))
    t.text = text or ""
    if text and (text.startswith(" ") or text.endswith(" ")):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return True


def set_content_control_lines(doc: Document, tag: str, lines: list[str]) -> bool:
    """
    Replace the content of a content control with multiple paragraphs (one per line).
    Used for inclusion/exclusion criteria lists.
    """
    sdt = find_content_control(doc, tag)
    if sdt is None:
        return False
    content = sdt.find(_w("sdtContent"))
    if content is None:
        return False

    for child in list(content):
        content.remove(child)

    for line in lines:
        p = etree.SubElement(content, _w("p"))
        r = etree.SubElement(p, _w("r"))
        t = etree.SubElement(r, _w("t"))
        t.text = line or ""
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return True


def clear_content_control(doc: Document, tag: str) -> bool:
    """
    Remove all content inside a content control, leaving a single empty paragraph.
    Used when the API returns no data for a tag so stale content from previous
    runs does not remain in the output document.
    Returns True if the control was found.
    """
    sdt = find_content_control(doc, tag)
    if sdt is None:
        return False
    content = sdt.find(_w("sdtContent"))
    if content is None:
        return False
    for child in list(content):
        content.remove(child)
    etree.SubElement(content, _w("p"))
    return True


def get_content_control_tags(doc: Document) -> list[str]:
    """Return all SB_* content control tag names found in the document."""
    tags = []
    for sdt in doc.element.body.iter(_w("sdt")):
        sdt_pr = sdt.find(_w("sdtPr"))
        if sdt_pr is None:
            continue
        tag_elem = sdt_pr.find(_w("tag"))
        if tag_elem is not None:
            val = tag_elem.get(_w("val"), "")
            if val.startswith("SB_"):
                tags.append(val)
    return tags
