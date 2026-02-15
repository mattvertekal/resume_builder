#!/usr/bin/env python3
"""Vertekal Resume DOCX Generator.

Takes structured JSON resume content and produces a .docx file matching
the Vertekal template exactly — branded header/footer, light blue section
headings, certification badges, and formatted bullet lists.

Approach: Copy the finished template docx, then replace document.xml and
document.xml.rels inside the ZIP while keeping everything else (styles,
numbering, headers, footers, media) intact.

No external dependencies — uses only Python 3.9+ stdlib.
"""

import argparse
import json
import os
import shutil
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates", "vertekal_template.docx")
BADGES_DIR = os.path.join(PROJECT_ROOT, "assets", "badges")

# OOXML Namespaces
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "o": "urn:schemas-microsoft-com:office:office",
    "v": "urn:schemas-microsoft-com:vml",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "cx1": "http://schemas.microsoft.com/office/drawing/2015/9/8/chartex",
    "cx2": "http://schemas.microsoft.com/office/drawing/2015/10/21/chartex",
    "cx3": "http://schemas.microsoft.com/office/drawing/2016/5/9/chartex",
    "cx4": "http://schemas.microsoft.com/office/drawing/2016/5/10/chartex",
    "cx5": "http://schemas.microsoft.com/office/drawing/2016/5/11/chartex",
    "cx6": "http://schemas.microsoft.com/office/drawing/2016/5/12/chartex",
    "cx7": "http://schemas.microsoft.com/office/drawing/2016/5/13/chartex",
    "cx8": "http://schemas.microsoft.com/office/drawing/2016/5/14/chartex",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "oel": "http://schemas.microsoft.com/office/2019/extlst",
    "w16du": "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
    "w16sdtfl": "http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock",
}

# Badge registry: key -> (filename, cx_emu, cy_emu, description)
BADGE_REGISTRY = {
    "csm": ("csm.png", 962025, 838200, "Scrum Alliance CSM Certified"),
    "ts_sci": ("ts_sci.png", 723900, 781050, "TS/SCI Clearance"),
    "aws_cloud_practitioner": ("aws_cloud_practitioner.png", 795478, 795478, "AWS Cloud Practitioner"),
    "security_plus": ("security_plus.png", 822960, 822960, "CompTIA Security+ Certified"),
}

# Badge horizontal positions for 4 badges (from the template, in EMU)
# Order in template: aws_cloud_practitioner, security_plus, csm, ts_sci
BADGE_POSITIONS_4 = {
    "aws_cloud_practitioner": (3219450, 76200),
    "security_plus": (4076700, 57150),
    "csm": (4905375, 57150),
    "ts_sci": (5848350, 95250),
}

# For fewer badges, center them by computing offsets
# The badge area spans roughly from x=3219450 to x=6572250 (rightmost edge of ts_sci)
BADGE_AREA_LEFT = 3219450
BADGE_AREA_RIGHT = 6572250
BADGE_AREA_CENTER = (BADGE_AREA_LEFT + BADGE_AREA_RIGHT) // 2
BADGE_VERTICAL_DEFAULT = 57150

# Relationship IDs: badges start at rId11 in the template
BADGE_RID_START = 11

# Header/footer relationship IDs (fixed from template)
HEADER_FOOTER_RELS = {
    "rId15": ("header", "header1.xml"),
    "rId16": ("header", "header2.xml"),
    "rId17": ("footer", "footer1.xml"),
    "rId18": ("footer", "footer2.xml"),
    "rId19": ("header", "header3.xml"),
    "rId20": ("footer", "footer3.xml"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def w(tag):
    """Create a tag in the w: namespace."""
    return f"{{{NS['w']}}}{tag}"


def w14(tag):
    return f"{{{NS['w14']}}}{tag}"


def r_ns(tag):
    return f"{{{NS['r']}}}{tag}"


def wp(tag):
    return f"{{{NS['wp']}}}{tag}"


def wp14(tag):
    return f"{{{NS['wp14']}}}{tag}"


def a(tag):
    return f"{{{NS['a']}}}{tag}"


def a14(tag):
    return f"{{{NS['a14']}}}{tag}"


def pic(tag):
    return f"{{{NS['pic']}}}{tag}"


def mc(tag):
    return f"{{{NS['mc']}}}{tag}"


def _set(el, ns_prefix, attr, value):
    """Set an attribute with namespace prefix."""
    el.set(f"{{{NS[ns_prefix]}}}{attr}", value)


# ---------------------------------------------------------------------------
# XML Builder Functions
# ---------------------------------------------------------------------------

def build_contact_paragraph(name, phone, email):
    """Contact line: centered, bold, Times New Roman."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    SubElement(pPr, w("jc"), {w("val"): "center"})
    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("b"))
    SubElement(rPr_p, w("bCs"))

    run = SubElement(p, w("r"))
    rPr = SubElement(run, w("rPr"))
    SubElement(rPr, w("b"))
    SubElement(rPr, w("bCs"))
    t = SubElement(run, w("t"))
    t.text = f"{name} | {phone} | {email}"

    return p


def build_section_heading(title):
    """Blue shaded section heading (#D3E2F1), centered, bold."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    SubElement(pPr, w("keepNext"))
    SubElement(pPr, w("keepLines"))
    pBdr = SubElement(pPr, w("pBdr"))
    for side in ("top", "left", "bottom", "right", "between"):
        SubElement(pBdr, w(side), {w("val"): "nil"})
    SubElement(pPr, w("shd"), {
        w("val"): "clear",
        w("color"): "auto",
        w("fill"): "D3E2F1",
    })
    SubElement(pPr, w("spacing"), {w("before"): "120", w("after"): "120"})
    SubElement(pPr, w("ind"), {
        w("left"): "-720",
        w("right"): "-720",
        w("firstLine"): "864",
    })
    SubElement(pPr, w("jc"), {w("val"): "center"})
    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("b"))
    SubElement(rPr_p, w("color"), {w("val"): "000000"})

    run = SubElement(p, w("r"))
    rPr = SubElement(run, w("rPr"))
    SubElement(rPr, w("b"))
    SubElement(rPr, w("bCs"))
    SubElement(rPr, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    t = SubElement(run, w("t"))
    t.text = title

    return p


def build_summary_paragraph(text):
    """NoSpacing style, centered, Times New Roman 11pt (sz=22)."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    SubElement(pPr, w("pStyle"), {w("val"): "NoSpacing"})
    SubElement(pPr, w("jc"), {w("val"): "center"})

    run = SubElement(p, w("r"))
    rPr = SubElement(run, w("rPr"))
    SubElement(rPr, w("rFonts"), {
        w("ascii"): "Times New Roman",
        w("eastAsia"): "Times New Roman",
        w("hAnsi"): "Times New Roman",
        w("cs"): "Times New Roman",
    })
    SubElement(rPr, w("sz"), {w("val"): "22"})
    t = SubElement(run, w("t"))
    t.text = text

    return p


def build_badge_anchor(rid, badge_key, pos_h, pos_v):
    """Build a wp:anchor drawing element for a single badge image."""
    cfg = BADGE_REGISTRY[badge_key]
    _, cx, cy, descr = cfg

    drawing = Element(w("drawing"))
    anchor = SubElement(drawing, wp("anchor"), {
        "distT": "0", "distB": "0", "distL": "114300", "distR": "114300",
        "simplePos": "0", "relativeHeight": "251659264",
        "behindDoc": "0", "locked": "0", "layoutInCell": "1",
        "allowOverlap": "1",
    })

    SubElement(anchor, wp("simplePos"), {"x": "0", "y": "0"})

    posH = SubElement(anchor, wp("positionH"), {"relativeFrom": "column"})
    SubElement(posH, wp("posOffset")).text = str(pos_h)

    posV = SubElement(anchor, wp("positionV"), {"relativeFrom": "paragraph"})
    SubElement(posV, wp("posOffset")).text = str(pos_v)

    SubElement(anchor, wp("extent"), {"cx": str(cx), "cy": str(cy)})
    SubElement(anchor, wp("effectExtent"), {"l": "0", "t": "0", "r": "0", "b": "0"})
    SubElement(anchor, wp("wrapNone"))
    SubElement(anchor, wp("docPr"), {"id": str(hash(badge_key) % 2000000000), "name": "drawing", "descr": descr})

    cNvGfp = SubElement(anchor, wp("cNvGraphicFramePr"))
    SubElement(cNvGfp, a("graphicFrameLocks"), {"noChangeAspect": "1"})

    graphic = SubElement(anchor, a("graphic"))
    graphicData = SubElement(graphic, a("graphicData"), {
        "uri": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    })

    pic_el = SubElement(graphicData, pic("pic"))
    nvPicPr = SubElement(pic_el, pic("nvPicPr"))
    SubElement(nvPicPr, pic("cNvPr"), {"id": str(hash(badge_key) % 2000000000), "name": ""})
    SubElement(nvPicPr, pic("cNvPicPr"))

    blipFill = SubElement(pic_el, pic("blipFill"))
    blip = SubElement(blipFill, a("blip"), {r_ns("embed"): rid})
    extLst = SubElement(blip, a("extLst"))
    ext = SubElement(extLst, a("ext"), {"uri": "{28A0092B-C50C-407E-A947-70E740481C1C}"})
    SubElement(ext, a14("useLocalDpi"), {"val": "0"})
    stretch = SubElement(blipFill, a("stretch"))
    SubElement(stretch, a("fillRect"))

    spPr = SubElement(pic_el, pic("spPr"))
    xfrm = SubElement(spPr, a("xfrm"))
    SubElement(xfrm, a("off"), {"x": "0", "y": "0"})
    SubElement(xfrm, a("ext"), {"cx": str(cx), "cy": str(cy)})
    prstGeom = SubElement(spPr, a("prstGeom"), {"prst": "rect"})
    SubElement(prstGeom, a("avLst"))

    sizeRelH = SubElement(anchor, wp14("sizeRelH"), {"relativeFrom": "page"})
    SubElement(sizeRelH, wp14("pctWidth")).text = "0"
    sizeRelV = SubElement(anchor, wp14("sizeRelV"), {"relativeFrom": "page"})
    SubElement(sizeRelV, wp14("pctHeight")).text = "0"

    return drawing


def compute_badge_positions(badge_keys):
    """Compute horizontal positions for badges based on count.

    For 4 badges, use the exact template positions.
    For fewer, center the subset within the badge area.
    """
    positions = {}
    if len(badge_keys) == 4:
        for key in badge_keys:
            if key in BADGE_POSITIONS_4:
                positions[key] = BADGE_POSITIONS_4[key]
            else:
                # Unknown badge, place it generically
                positions[key] = (BADGE_AREA_CENTER, BADGE_VERTICAL_DEFAULT)
    else:
        # Distribute badges evenly across the badge area
        total_width = sum(BADGE_REGISTRY[k][1] for k in badge_keys if k in BADGE_REGISTRY)
        gap = 100000  # ~0.1 inch gap between badges
        total_span = total_width + gap * (len(badge_keys) - 1) if len(badge_keys) > 1 else total_width
        start_x = BADGE_AREA_CENTER - total_span // 2
        current_x = start_x
        for key in badge_keys:
            if key in BADGE_REGISTRY:
                positions[key] = (current_x, BADGE_VERTICAL_DEFAULT)
                current_x += BADGE_REGISTRY[key][1] + gap
    return positions


def build_education_paragraph(degree, university, badge_keys, badge_rids):
    """Education text + anchored badge images in a single paragraph."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("sz"), {w("val"): "22"})

    positions = compute_badge_positions(badge_keys)

    # Badge drawings — each as a separate run
    for key in badge_keys:
        if key not in BADGE_REGISTRY or key not in badge_rids:
            continue
        rid = badge_rids[key]
        pos_h, pos_v = positions.get(key, (BADGE_AREA_CENTER, BADGE_VERTICAL_DEFAULT))

        run = SubElement(p, w("r"))
        rPr = SubElement(run, w("rPr"))
        SubElement(rPr, w("noProof"))
        SubElement(rPr, w("sz"), {w("val"): "22"})
        drawing = build_badge_anchor(rid, key, pos_h, pos_v)
        run.append(drawing)

    # Degree text
    run_deg = SubElement(p, w("r"))
    rPr_deg = SubElement(run_deg, w("rPr"))
    SubElement(rPr_deg, w("sz"), {w("val"): "22"})
    SubElement(rPr_deg, w("szCs"), {w("val"): "22"})
    t_deg = SubElement(run_deg, w("t"))
    t_deg.text = degree

    # Line break
    run_br = SubElement(p, w("r"))
    rPr_br = SubElement(run_br, w("rPr"))
    SubElement(rPr_br, w("sz"), {w("val"): "22"})
    SubElement(run_br, w("br"))

    # University (bold)
    run_uni = SubElement(p, w("r"))
    rPr_uni = SubElement(run_uni, w("rPr"))
    SubElement(rPr_uni, w("b"))
    SubElement(rPr_uni, w("bCs"))
    SubElement(rPr_uni, w("sz"), {w("val"): "22"})
    SubElement(rPr_uni, w("szCs"), {w("val"): "22"})
    t_uni = SubElement(run_uni, w("t"))
    t_uni.text = university

    return p


def build_empty_paragraph(sz="22", bold=False):
    """Empty spacer paragraph."""
    p = Element(w("p"))
    if sz or bold:
        pPr = SubElement(p, w("pPr"))
        rPr = SubElement(pPr, w("rPr"))
        if bold:
            SubElement(rPr, w("b"))
            SubElement(rPr, w("bCs"))
        if sz:
            SubElement(rPr, w("sz"), {w("val"): sz})
    return p


def build_job_title_paragraph(title, dates, has_company=False):
    """Job title (bold) + date (non-bold), 11pt."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))

    if not has_company:
        # Add borders (nil) matching template for non-company jobs
        pBdr = SubElement(pPr, w("pBdr"))
        for side in ("top", "left", "bottom", "right", "between"):
            SubElement(pBdr, w(side), {w("val"): "nil"})

    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("b"))
    SubElement(rPr_p, w("bCs"))
    SubElement(rPr_p, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    SubElement(rPr_p, w("sz"), {w("val"): "22"})

    # Title run (bold)
    run_title = SubElement(p, w("r"))
    rPr_t = SubElement(run_title, w("rPr"))
    SubElement(rPr_t, w("b"))
    SubElement(rPr_t, w("bCs"))
    SubElement(rPr_t, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    SubElement(rPr_t, w("sz"), {w("val"): "22"})
    SubElement(rPr_t, w("szCs"), {w("val"): "22"})
    t_title = SubElement(run_title, w("t"), {"{http://www.w3.org/XML/1998/namespace}space": "preserve"})
    t_title.text = f"{title} - "

    # Date run (non-bold)
    run_date = SubElement(p, w("r"))
    rPr_d = SubElement(run_date, w("rPr"))
    SubElement(rPr_d, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    SubElement(rPr_d, w("sz"), {w("val"): "22"})
    SubElement(rPr_d, w("szCs"), {w("val"): "22"})
    t_date = SubElement(run_date, w("t"))
    t_date.text = dates

    return p


def build_company_paragraph(company):
    """Company name paragraph (for military roles)."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    pBdr = SubElement(pPr, w("pBdr"))
    for side in ("top", "left", "bottom", "right", "between"):
        SubElement(pBdr, w(side), {w("val"): "nil"})
    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    SubElement(rPr_p, w("sz"), {w("val"): "22"})

    run = SubElement(p, w("r"))
    rPr = SubElement(run, w("rPr"))
    SubElement(rPr, w("color"), {w("val"): "000000", w("themeColor"): "text1"})
    SubElement(rPr, w("sz"), {w("val"): "22"})
    SubElement(rPr, w("szCs"), {w("val"): "22"})
    t = SubElement(run, w("t"))
    t.text = company

    return p


def build_bullet_paragraph(text):
    """ListParagraph with numId=62, 10pt, line spacing 300."""
    p = Element(w("p"))
    pPr = SubElement(p, w("pPr"))
    SubElement(pPr, w("pStyle"), {w("val"): "ListParagraph"})
    numPr = SubElement(pPr, w("numPr"))
    SubElement(numPr, w("ilvl"), {w("val"): "0"})
    SubElement(numPr, w("numId"), {w("val"): "62"})
    SubElement(pPr, w("spacing"), {
        w("before"): "240",
        w("after"): "240",
        w("line"): "300",
        w("lineRule"): "auto",
    })
    rPr_p = SubElement(pPr, w("rPr"))
    SubElement(rPr_p, w("sz"), {w("val"): "20"})
    SubElement(rPr_p, w("szCs"), {w("val"): "20"})

    run = SubElement(p, w("r"))
    rPr = SubElement(run, w("rPr"))
    SubElement(rPr, w("sz"), {w("val"): "20"})
    SubElement(rPr, w("szCs"), {w("val"): "20"})
    t = SubElement(run, w("t"))
    t.text = text

    return p


def build_sect_pr():
    """Section properties with header/footer references and page setup."""
    sectPr = Element(w("sectPr"))

    # Header/footer references
    SubElement(sectPr, w("headerReference"), {w("type"): "even", r_ns("id"): "rId15"})
    SubElement(sectPr, w("headerReference"), {w("type"): "default", r_ns("id"): "rId16"})
    SubElement(sectPr, w("footerReference"), {w("type"): "even", r_ns("id"): "rId17"})
    SubElement(sectPr, w("footerReference"), {w("type"): "default", r_ns("id"): "rId18"})
    SubElement(sectPr, w("headerReference"), {w("type"): "first", r_ns("id"): "rId19"})
    SubElement(sectPr, w("footerReference"), {w("type"): "first", r_ns("id"): "rId20"})

    SubElement(sectPr, w("pgSz"), {w("w"): "12240", w("h"): "15840"})
    SubElement(sectPr, w("pgMar"), {
        w("top"): "720", w("right"): "720", w("bottom"): "720", w("left"): "720",
        w("header"): "0", w("footer"): "0", w("gutter"): "0",
    })
    SubElement(sectPr, w("pgNumType"), {w("start"): "1"})
    SubElement(sectPr, w("cols"), {w("space"): "720"})
    SubElement(sectPr, w("docGrid"), {w("linePitch"): "272"})

    return sectPr


# ---------------------------------------------------------------------------
# Document Assembly
# ---------------------------------------------------------------------------

def build_document_xml(data):
    """Build the complete document.xml content from JSON data."""

    # Register all namespaces to avoid ns0/ns1 prefixes
    import xml.etree.ElementTree as ET
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)

    # Root element — register_namespace handles xmlns declarations automatically
    doc = Element(w("document"))
    doc.set(mc("Ignorable"), "w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14")

    body = SubElement(doc, w("body"))

    # -- Contact --
    body.append(build_contact_paragraph(data["name"], data["phone"], data["email"]))

    # -- Professional Experience Summary heading --
    body.append(build_section_heading("Professional Experience Summary"))

    # -- Summary text --
    body.append(build_summary_paragraph(data["summary"]))

    # -- Education & Certifications heading --
    body.append(build_section_heading("Education & Certifications"))

    # -- Education + badges --
    badge_keys = data.get("badges", [])
    badge_rids = {}
    rid_num = BADGE_RID_START
    for key in badge_keys:
        if key in BADGE_REGISTRY:
            badge_rids[key] = f"rId{rid_num}"
            rid_num += 1

    body.append(build_education_paragraph(
        data["education"]["degree"],
        data["education"]["university"],
        badge_keys,
        badge_rids,
    ))

    # Spacer paragraphs after education (to give room for badge images)
    body.append(build_empty_paragraph("22", bold=True))
    body.append(build_empty_paragraph())
    body.append(build_empty_paragraph("22", bold=True))
    body.append(build_empty_paragraph("22", bold=True))

    # -- Professional Experience heading --
    body.append(build_section_heading("Professional Experience"))

    # -- Jobs --
    for job in data["jobs"]:
        has_company = bool(job.get("company"))
        body.append(build_job_title_paragraph(job["title"], job["dates"], has_company))

        if has_company:
            body.append(build_company_paragraph(job["company"]))

        for bullet in job["bullets"]:
            body.append(build_bullet_paragraph(bullet))

    # Trailing spacer
    body.append(build_empty_paragraph("22"))
    body.append(build_empty_paragraph("22"))

    # -- Section properties --
    body.append(build_sect_pr())

    # Serialize
    xml_decl = '<?xml version="1.0" encoding="UTF-8"?>'
    body_str = tostring(doc, encoding="unicode")
    return xml_decl + body_str


def build_document_rels(badge_keys):
    """Build document.xml.rels with correct badge image relationships."""
    import xml.etree.ElementTree as ET

    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    ET.register_namespace("", rel_ns)

    root = Element(f"{{{rel_ns}}}Relationships")

    # Fixed relationships (non-badge)
    fixed_rels = [
        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml", "../customXml/item1.xml"),
        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml", "../customXml/item2.xml"),
        ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml", "../customXml/item3.xml"),
        ("rId4", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml", "../customXml/item4.xml"),
        ("rId5", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering", "numbering.xml"),
        ("rId6", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "styles.xml"),
        ("rId7", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings", "settings.xml"),
        ("rId8", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/webSettings", "webSettings.xml"),
        ("rId9", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes", "footnotes.xml"),
        ("rId10", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes", "endnotes.xml"),
    ]

    for rid, rtype, target in fixed_rels:
        SubElement(root, f"{{{rel_ns}}}Relationship", {
            "Id": rid, "Type": rtype, "Target": target,
        })

    # Badge image relationships (rId11+)
    rid_num = BADGE_RID_START
    image_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    for key in badge_keys:
        if key in BADGE_REGISTRY:
            filename = BADGE_REGISTRY[key][0]
            SubElement(root, f"{{{rel_ns}}}Relationship", {
                "Id": f"rId{rid_num}",
                "Type": image_type,
                "Target": f"media/{filename}",
            })
            rid_num += 1

    # Header/footer relationships (rId15-rId20)
    hf_type_map = {
        "header": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
        "footer": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
    }
    for rid, (hf_type, target) in HEADER_FOOTER_RELS.items():
        SubElement(root, f"{{{rel_ns}}}Relationship", {
            "Id": rid, "Type": hf_type_map[hf_type], "Target": target,
        })

    # Font table and theme
    SubElement(root, f"{{{rel_ns}}}Relationship", {
        "Id": "rId21",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable",
        "Target": "fontTable.xml",
    })
    SubElement(root, f"{{{rel_ns}}}Relationship", {
        "Id": "rId22",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
        "Target": "theme/theme1.xml",
    })

    xml_decl = '<?xml version="1.0" encoding="utf-8"?>'
    return xml_decl + tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
# DOCX Assembly
# ---------------------------------------------------------------------------

def generate_resume(input_path, output_path, template_path=None):
    """Generate a Vertekal resume .docx from JSON input."""
    if template_path is None:
        template_path = TEMPLATE_PATH

    # Load input JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Copy template to output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    shutil.copy2(template_path, output_path)

    badge_keys = [k for k in data.get("badges", []) if k in BADGE_REGISTRY]

    # Build new XML content
    doc_xml = build_document_xml(data)
    rels_xml = build_document_rels(badge_keys)

    # Replace files inside the ZIP
    _replace_in_zip(output_path, {
        "word/document.xml": doc_xml.encode("utf-8"),
        "word/_rels/document.xml.rels": rels_xml.encode("utf-8"),
    }, badge_keys)

    print(f"Generated: {output_path}")


def _replace_in_zip(zip_path, replacements, badge_keys):
    """Replace specific files inside a ZIP and manage badge images.

    Args:
        zip_path: Path to the .docx (ZIP) file.
        replacements: Dict of {archive_path: bytes_content} to replace.
        badge_keys: List of badge keys to include.
    """
    import tempfile

    # Template badge filenames (image1-4.png) that may need to be removed/replaced
    template_badge_files = {"word/media/image1.png", "word/media/image2.png",
                            "word/media/image3.png", "word/media/image4.png"}

    # Badge files we need (using their proper names)
    needed_badge_files = set()
    for key in badge_keys:
        if key in BADGE_REGISTRY:
            needed_badge_files.add(f"word/media/{BADGE_REGISTRY[key][0]}")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(zip_path, "r") as zin:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename in replacements:
                        # Write our replacement content
                        zout.writestr(item, replacements[item.filename])
                    elif item.filename in template_badge_files:
                        # Skip old template badge images — we'll add new ones
                        pass
                    else:
                        # Copy everything else as-is
                        zout.writestr(item, zin.read(item.filename))

                # Add the correct badge images from assets
                for key in badge_keys:
                    if key in BADGE_REGISTRY:
                        filename = BADGE_REGISTRY[key][0]
                        src_path = os.path.join(BADGES_DIR, filename)
                        archive_path = f"word/media/{filename}"
                        if os.path.exists(src_path):
                            zout.write(src_path, archive_path)
                        else:
                            print(f"Warning: Badge image not found: {src_path}")

        # Replace original with modified
        shutil.move(tmp_path, zip_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Vertekal-branded resume .docx from JSON input.",
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to the JSON input file.",
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Path for the output .docx file.",
    )
    parser.add_argument(
        "--template", "-t", default=None,
        help=f"Path to the template .docx file (default: {TEMPLATE_PATH}).",
    )
    args = parser.parse_args()

    generate_resume(args.input, args.output, args.template)


if __name__ == "__main__":
    main()
