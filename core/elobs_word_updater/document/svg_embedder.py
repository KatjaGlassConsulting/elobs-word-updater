from __future__ import annotations
import base64
import re
import uuid
from lxml import etree
from docx import Document
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from .content_controls import find_content_control

# Namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

# Minimal 1x1 transparent PNG as a fallback for old Word versions
_FALLBACK_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIA"
    "BQABNjN9GQAAAABJRkJggg=="
)
FALLBACK_PNG = base64.b64decode(_FALLBACK_PNG_B64)

# Default size when SVG dimensions cannot be parsed (6 inches wide, 4 inches tall)
DEFAULT_CX_EMU = 5_486_400
DEFAULT_CY_EMU = 3_657_600
EMU_PER_PX_96DPI = 9525  # 914400 / 96


def _parse_svg_dimensions(svg_bytes: bytes) -> tuple[int, int]:
    """Parse width/height from SVG root element. Returns (cx_emu, cy_emu)."""
    try:
        root = etree.fromstring(svg_bytes)
        w_str = root.get("width", "")
        h_str = root.get("height", "")

        def to_emu(val: str) -> int | None:
            val = val.strip()
            if val.endswith("px"):
                return int(float(val[:-2]) * EMU_PER_PX_96DPI)
            if val.endswith("pt"):
                return int(float(val[:-2]) * 12700)
            if val.endswith("cm"):
                return int(float(val[:-2]) * 360000)
            if val.endswith("mm"):
                return int(float(val[:-2]) * 36000)
            if val.endswith("in"):
                return int(float(val[:-2]) * 914400)
            try:
                return int(float(val) * EMU_PER_PX_96DPI)
            except ValueError:
                return None

        cx = to_emu(w_str)
        cy = to_emu(h_str)

        # Try viewBox as fallback
        if cx is None or cy is None:
            vb = root.get("viewBox", "")
            parts = re.split(r"[\s,]+", vb.strip())
            if len(parts) == 4:
                cx = int(float(parts[2]) * EMU_PER_PX_96DPI)
                cy = int(float(parts[3]) * EMU_PER_PX_96DPI)

        return (cx or DEFAULT_CX_EMU, cy or DEFAULT_CY_EMU)
    except Exception:
        return (DEFAULT_CX_EMU, DEFAULT_CY_EMU)


def _add_image_part(doc: Document, blob: bytes, content_type: str, ext: str) -> str:
    """Add a binary image part to the document and return its relationship ID."""
    part_name = PackURI(f"/word/media/osb_{uuid.uuid4().hex[:8]}{ext}")
    part = Part(part_name, content_type, blob, doc.part.package)
    return doc.part.relate_to(part, IMAGE_REL)


def _build_drawing_xml(svg_rId: str, png_rId: str, cx: int, cy: int, img_id: int) -> etree._Element:
    """Build the <w:drawing> XML element that embeds an SVG with a PNG fallback."""
    ns = {
        "w": W_NS,
        "wp": WP_NS,
        "a": A_NS,
        "pic": PIC_NS,
        "r": R_NS,
        "asvg": ASVG_NS,
    }

    xml_str = f"""
<w:drawing xmlns:w="{W_NS}">
  <wp:inline distT="0" distB="0" distL="0" distR="0"
             xmlns:wp="{WP_NS}">
    <wp:extent cx="{cx}" cy="{cy}"/>
    <wp:effectExtent l="0" t="0" r="0" b="0"/>
    <wp:docPr id="{img_id}" name="OSB_SVG_{img_id}"/>
    <wp:cNvGraphicFramePr>
      <a:graphicFrameLocks xmlns:a="{A_NS}" noChangeAspect="1"/>
    </wp:cNvGraphicFramePr>
    <a:graphic xmlns:a="{A_NS}">
      <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic xmlns:pic="{PIC_NS}">
          <pic:nvPicPr>
            <pic:cNvPr id="0" name="OSB_SVG_{img_id}"/>
            <pic:cNvPicPr preferRelativeResize="0"/>
          </pic:nvPicPr>
          <pic:blipFill>
            <a:blip xmlns:r="{R_NS}" r:embed="{png_rId}">
              <a:extLst>
                <a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}">
                  <asvg:svgBlip xmlns:asvg="{ASVG_NS}"
                                xmlns:r="{R_NS}"
                                r:embed="{svg_rId}"/>
                </a:ext>
              </a:extLst>
            </a:blip>
            <a:stretch><a:fillRect/></a:stretch>
          </pic:blipFill>
          <pic:spPr>
            <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          </pic:spPr>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
""".strip()
    return etree.fromstring(xml_str)


def embed_svg_at_content_control(doc: Document, tag: str, svg_bytes: bytes) -> bool:
    """
    Replace the content control identified by `tag` with a native Word SVG image.
    Uses a 1x1 transparent PNG as a fallback for older Word versions.

    Returns True if the control was found and updated.
    """
    sdt = find_content_control(doc, tag)
    if sdt is None:
        return False

    sdt_content = sdt.find(f"{{{W_NS}}}sdtContent")
    if sdt_content is None:
        return False

    cx, cy = _parse_svg_dimensions(svg_bytes)
    svg_rId = _add_image_part(doc, svg_bytes, "image/svg+xml", ".svg")
    png_rId = _add_image_part(doc, FALLBACK_PNG, "image/png", ".png")

    # Use a simple incrementing ID based on existing drawings
    img_id = len(list(doc.element.body.iter(f"{{{W_NS}}}drawing"))) + 1

    drawing = _build_drawing_xml(svg_rId, png_rId, cx, cy, img_id)

    W = f"{{{W_NS}}}"
    p = etree.Element(f"{W}p")
    r = etree.SubElement(p, f"{W}r")
    r.append(drawing)

    for child in list(sdt_content):
        sdt_content.remove(child)
    sdt_content.append(p)

    return True
