from __future__ import annotations
from pathlib import Path
import pytest
from docx import Document
from lxml import etree
from elobs_word_updater.document.svg_embedder import (
    embed_svg_at_content_control,
    _parse_svg_dimensions,
    DEFAULT_CX_EMU,
    DEFAULT_CY_EMU,
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FIXTURES = Path(__file__).parent / "fixtures"

SAMPLE_SVG = b"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400px" height="200px">
  <rect x="10" y="10" width="380" height="180" fill="blue"/>
</svg>"""


def _make_doc_with_cc(tag: str) -> Document:
    doc = Document()
    xml = f"""
<w:sdt xmlns:w="{W_NS}">
  <w:sdtPr><w:tag w:val="{tag}"/></w:sdtPr>
  <w:sdtContent><w:p><w:r><w:t>placeholder</w:t></w:r></w:p></w:sdtContent>
</w:sdt>""".strip()
    doc.element.body.insert(0, etree.fromstring(xml))
    return doc


def test_parse_svg_dimensions_px():
    """Parses pixel dimensions (400px × 200px) and converts to EMU."""
    cx, cy = _parse_svg_dimensions(SAMPLE_SVG)
    assert cx == 400 * 9525
    assert cy == 200 * 9525


def test_parse_svg_dimensions_fallback():
    """Falls back to default dimensions when SVG has no width, height, or viewBox."""
    bad_svg = b"<svg xmlns='http://www.w3.org/2000/svg'/>"
    cx, cy = _parse_svg_dimensions(bad_svg)
    assert cx == DEFAULT_CX_EMU
    assert cy == DEFAULT_CY_EMU


def test_embed_svg_replaces_content_control():
    """Embeds SVG into the content control; sdt wrapper is preserved with a drawing element inside."""
    doc = _make_doc_with_cc("SB_StudydesignGraphic")
    result = embed_svg_at_content_control(doc, "SB_StudydesignGraphic", SAMPLE_SVG)
    assert result is True
    # The sdt wrapper stays; only its inner content is replaced with a drawing
    from elobs_word_updater.document.content_controls import find_content_control
    assert find_content_control(doc, "SB_StudydesignGraphic") is not None
    # A drawing element should now exist inside the sdt
    drawings = list(doc.element.body.iter(f"{{{W_NS}}}drawing"))
    assert len(drawings) == 1


def test_embed_svg_missing_tag():
    """Returns False when the target content control tag does not exist."""
    doc = _make_doc_with_cc("SB_StudydesignGraphic")
    result = embed_svg_at_content_control(doc, "SB_DoesNotExist", SAMPLE_SVG)
    assert result is False


def test_embed_real_svg_fixture():
    """Test with the actual SVG fetched from the API."""
    svg_path = FIXTURES / "design.svg"
    if not svg_path.exists():
        pytest.skip("design.svg fixture not available")
    svg_bytes = svg_path.read_bytes()
    doc = _make_doc_with_cc("SB_StudydesignGraphic")
    result = embed_svg_at_content_control(doc, "SB_StudydesignGraphic", svg_bytes)
    assert result is True


def test_parse_svg_dimensions_pt():
    """Parses point dimensions and converts to EMU."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="100pt" height="50pt"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(100 * 12700)
    assert cy == int(50 * 12700)


def test_parse_svg_dimensions_cm():
    """Parses centimetre dimensions and converts to EMU."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10cm" height="5cm"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(10 * 360000)
    assert cy == int(5 * 360000)


def test_parse_svg_dimensions_mm():
    """Parses millimetre dimensions and converts to EMU."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(100 * 36000)
    assert cy == int(50 * 36000)


def test_parse_svg_dimensions_in():
    """Parses inch dimensions and converts to EMU."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="2in" height="1in"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(2 * 914400)
    assert cy == int(1 * 914400)


def test_parse_svg_dimensions_unitless_treated_as_px():
    """Treats bare numeric width/height values as pixels."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(300 * 9525)
    assert cy == int(150 * 9525)


def test_parse_svg_dimensions_viewbox_fallback():
    """Falls back to viewBox when width/height attributes are missing."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"/>'
    cx, cy = _parse_svg_dimensions(svg)
    assert cx == int(800 * 9525)
    assert cy == int(400 * 9525)


def test_parse_svg_dimensions_invalid_xml_uses_defaults():
    """Invalid XML bytes fall back to default EMU dimensions."""
    cx, cy = _parse_svg_dimensions(b"not valid xml at all!!!")
    assert cx == DEFAULT_CX_EMU
    assert cy == DEFAULT_CY_EMU


def test_embed_svg_content_control_content_replaced():
    """The placeholder text inside the sdt should be gone after embed."""
    doc = _make_doc_with_cc("SB_StudydesignGraphic")
    embed_svg_at_content_control(doc, "SB_StudydesignGraphic", SAMPLE_SVG)
    texts = [t.text for t in doc.element.body.iter(f"{{{W_NS}}}t") if t.text]
    assert "placeholder" not in texts


def test_embed_svg_adds_two_image_parts():
    """One SVG part and one fallback PNG part should be added to the package."""
    doc = _make_doc_with_cc("SB_StudydesignGraphic")
    parts_before = set(p.partname for p in doc.part.package.iter_parts())
    embed_svg_at_content_control(doc, "SB_StudydesignGraphic", SAMPLE_SVG)
    parts_after = set(p.partname for p in doc.part.package.iter_parts())
    new_parts = parts_after - parts_before
    extensions = {str(p).split(".")[-1] for p in new_parts}
    assert "svg" in extensions
    assert "png" in extensions


def test_embed_svg_drawing_ids_increment_for_multiple_embeds():
    """Each subsequent SVG embed gets a higher drawing ID than the previous."""
    doc = Document()
    for i, tag in enumerate(["SB_StudydesignGraphic", "SB_OtherGraphic"]):
        xml = f'<w:sdt xmlns:w="{W_NS}"><w:sdtPr><w:tag w:val="{tag}"/></w:sdtPr><w:sdtContent><w:p><w:r><w:t>ph</w:t></w:r></w:p></w:sdtContent></w:sdt>'
        doc.element.body.append(etree.fromstring(xml))
    embed_svg_at_content_control(doc, "SB_StudydesignGraphic", SAMPLE_SVG)
    embed_svg_at_content_control(doc, "SB_OtherGraphic", SAMPLE_SVG)
    drawings = list(doc.element.body.iter(f"{{{W_NS}}}drawing"))
    assert len(drawings) == 2
