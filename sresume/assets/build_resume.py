#!/usr/bin/env python3
"""
build_resume.py - ATS-safe Microsoft Word resume builder for the `sresume` skill.

Takes a structured JSON resume and emits a professionally typeset .docx,
plus optional plain-text (ATS) and markdown (LinkedIn/paste) renderings.

Design constraints (do not "improve" these away):
  * No tables, text boxes, columns, images or headers/footers holding content.
    Every ATS parses a single-column linear document correctly; nothing else
    is guaranteed to survive.
  * Dates are right-aligned with a right tab stop inside the same paragraph as
    the employer/title. This keeps role, company and dates as ONE logical line
    for the parser while still looking properly typeset.
  * Real Word Heading-like styling carries section titles so parsers and human
    readers both detect structure.
  * keep_with_next and widow control are set so headings never strand at a page
    foot and a bullet does not split one line across a page break.

Usage:
    python build_resume.py resume.json -o Sai_Principal_Architect.docx
    python build_resume.py resume.json -o out.docx --preset ats
    python build_resume.py resume.json -o out.docx --fit 2
    python build_resume.py resume.json --txt out.txt --md out.md
    python build_resume.py --schema

Requires: python-docx  (python -m pip install python-docx)
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_TAB_ALIGNMENT, WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import Pt, Inches, RGBColor
except ImportError:
    sys.exit("python-docx is required.  Run:  python -m pip install python-docx")


# --------------------------------------------------------------------------
# Typography presets. These control APPEARANCE ONLY.
# Which content appears, and in what order, is the persona's decision - see
# SKILL.md section 20. A preset never edits words.
# --------------------------------------------------------------------------
PRESETS = {
    # Maximum parseability. Black only, no rules, ubiquitous font. Use when the
    # application goes through an unknown or old ATS.
    "ats": {
        "font": "Calibri", "body": 11.0, "name": 20.0, "heading": 11.5,
        "accent": "000000", "rules": False, "space_after": 4.0,
        "section_before": 10.0, "bullet_space": 3.0, "headline_caps": False,
    },
    # Default. Clean, scannable, quietly modern. Safe with every modern ATS.
    "recruiter": {
        "font": "Calibri", "body": 10.5, "name": 22.0, "heading": 11.0,
        "accent": "1F3864", "rules": True, "space_after": 4.0,
        "section_before": 11.0, "bullet_space": 3.0, "headline_caps": False,
    },
    # Denser, for engineers who need systems detail on the page.
    "technical": {
        "font": "Calibri", "body": 10.0, "name": 20.0, "heading": 10.5,
        "accent": "1F3864", "rules": True, "space_after": 3.0,
        "section_before": 9.0, "bullet_space": 2.0, "headline_caps": False,
    },
    # Principal / architect. Serif, a little more air, authoritative.
    "principal": {
        "font": "Georgia", "body": 10.0, "name": 20.0, "heading": 10.5,
        "accent": "1F3864", "rules": True, "space_after": 4.0,
        "section_before": 11.0, "bullet_space": 3.0, "headline_caps": False,
    },
    # Executive. Generous white space, restrained, fewer but heavier lines.
    "executive": {
        "font": "Georgia", "body": 10.5, "name": 23.0, "heading": 11.0,
        "accent": "1F3864", "rules": True, "space_after": 5.0,
        "section_before": 13.0, "bullet_space": 4.0, "headline_caps": True,
    },
    # Consulting / client-facing profile.
    "consulting": {
        "font": "Calibri", "body": 10.5, "name": 21.0, "heading": 11.0,
        "accent": "1F3864", "rules": True, "space_after": 4.0,
        "section_before": 11.0, "bullet_space": 3.0, "headline_caps": False,
    },
}

BULLET = "•"

# Nested-bullet markers and indents, cascading the way Word's default
# multilevel list does. Depth beyond the list reuses the last entry.
MARKERS = ["•", "o", "▪", "-"]
LEVEL_INDENT = [0.16, 0.42, 0.68, 0.94]


# --------------------------------------------------------------------------
# low-level docx helpers
# --------------------------------------------------------------------------
def _set_doc_font(doc, name, size_pt):
    style = doc.styles["Normal"]
    style.font.name = name
    style.font.size = Pt(size_pt)
    style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    # python-docx only sets w:ascii; Word needs eastAsia/hAnsi/cs too or it
    # silently falls back to Times New Roman for some glyphs.
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)
    pf = style.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    pf.widow_control = True


def _bottom_rule(paragraph, color, size=6):
    """Thin rule under a section heading."""
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    p_pr.append(borders)


def _letter_space(paragraph, twentieths=20):
    for r in paragraph.runs:
        rpr = r._element.get_or_add_rPr()
        spacing = OxmlElement("w:spacing")
        spacing.set(qn("w:val"), str(twentieths))
        rpr.append(spacing)


def _no_proof(paragraph):
    """Suppress spell/grammar squiggles on technology-dense lines."""
    p_pr = paragraph._p.get_or_add_pPr()
    rpr = p_pr.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        p_pr.insert(0, rpr)
    rpr.append(OxmlElement("w:noProof"))


def _para(doc, space_before=0, space_after=0, align=None, keep=False,
          indent=None, hanging=None, tab_right=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.0
    pf.widow_control = True
    if align is not None:
        p.alignment = align
    if keep:
        pf.keep_with_next = True
    if indent is not None:
        pf.left_indent = Inches(indent)
    if hanging is not None:
        pf.first_line_indent = Inches(-hanging)
    if tab_right is not None:
        pf.tab_stops.add_tab_stop(Inches(tab_right), WD_TAB_ALIGNMENT.RIGHT)
    return p


def _run(p, text, bold=False, italic=False, size=None, color=None,
         caps=False, name=None):
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    if caps:
        r.font.all_caps = True
    if name:
        r.font.name = name
        rpr = r._element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), name)
    return r


# --------------------------------------------------------------------------
# page-fill estimation
# --------------------------------------------------------------------------
# Average glyph advance as a fraction of point size for the supported faces at
# resume-typical mixed case. Used only to ESTIMATE how many rendered lines a
# paragraph consumes. Word remains the authority.
_CHAR_W = {"Calibri": 0.475, "Georgia": 0.520, "Arial": 0.500,
           "Helvetica": 0.500, "Garamond": 0.450, "Cambria": 0.490}


def _wrapped_lines(text, font, size_pt, width_in):
    if not text:
        return 1
    per_char_in = (_CHAR_W.get(font, 0.50) * size_pt) / 72.0
    chars_per_line = max(10, int(width_in / per_char_in))
    total = 0
    for hard_line in str(text).split("\n"):
        words = hard_line.split()
        if not words:
            total += 1
            continue
        extra, line_len = 0, 0
        for w in words:
            add = len(w) + (1 if line_len else 0)
            if line_len + add > chars_per_line and line_len:
                extra += 1
                line_len = len(w)
            else:
                line_len += add
        total += extra + 1
    return max(1, total)


class FillMeter:
    """Accumulates estimated vertical points consumed."""

    def __init__(self, cfg, page_h, margins):
        self.cfg = cfg
        self.usable_pts = (page_h - margins[0] - margins[1]) * 72.0
        self.pts = 0.0

    def add(self, text, size, width_in, space=0.0, font=None):
        lines = _wrapped_lines(text, font or self.cfg["font"], size, width_in)
        self.pts += lines * size * 1.16 + space

    def pages(self):
        return self.pts / self.usable_pts


# --------------------------------------------------------------------------
# inline **bold** support
# --------------------------------------------------------------------------
def _split_bold(text):
    parts, last = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        if m.start() > last:
            parts.append((text[last:m.start()], False))
        parts.append((m.group(1), True))
        last = m.end()
    if last < len(text):
        parts.append((text[last:], False))
    return parts or [(text, False)]


# --------------------------------------------------------------------------
# section renderers
# --------------------------------------------------------------------------
def _heading(doc, cfg, title, meter, width):
    p = _para(doc, space_before=cfg["section_before"], space_after=3.0, keep=True)
    _run(p, title.upper(), bold=True, size=cfg["heading"],
         color=cfg["accent"], caps=True)
    _letter_space(p, 20)
    if cfg["rules"]:
        _bottom_rule(p, cfg["accent"])
    meter.add(title, cfg["heading"], width, space=cfg["section_before"] + 5.0)


def _bullet_list(doc, cfg, bullets, meter, width, depth=0, indent=None):
    """Render a bullet list, recursing into `children` for nested levels.

    A bullet is either a plain string or {"text": ..., "children": [...]}.
    Markers and indents cascade the way Word's default multilevel list does,
    so a resume that uses sub-bullets keeps its structure instead of being
    flattened. A parent that has children gets keep_with_next so a label like
    "Technology:" cannot strand at the foot of a page."""
    for b in bullets:
        if isinstance(b, dict):
            text = b.get("text", "")
            children = b.get("children") or []
        else:
            text, children = str(b), []
        ind = LEVEL_INDENT[min(depth, len(LEVEL_INDENT) - 1)] if indent is None \
            else indent
        marker = MARKERS[min(depth, len(MARKERS) - 1)]
        p = _para(doc, space_after=cfg["bullet_space"], indent=ind,
                  hanging=0.16, keep=bool(children))
        _run(p, marker + "  ")
        for chunk, is_bold in _split_bold(text):
            _run(p, chunk, bold=is_bold)
        _no_proof(p)
        meter.add(text, cfg["body"], width - ind, space=cfg["bullet_space"])
        if children:
            _bullet_list(doc, cfg, children, meter, width, depth + 1)


def _render_header(doc, cfg, header, meter, width):
    name = header.get("name", "")
    p = _para(doc, space_after=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    _run(p, name, bold=True, size=cfg["name"], color=cfg["accent"], caps=True)
    _letter_space(p, 30)
    meter.add(name, cfg["name"], width, space=2.0)

    headline = header.get("headline")
    if headline:
        p = _para(doc, space_after=3.0, align=WD_ALIGN_PARAGRAPH.CENTER)
        _run(p, headline, bold=True, size=cfg["body"] + 0.5,
             caps=cfg["headline_caps"])
        _no_proof(p)
        meter.add(headline, cfg["body"] + 1, width, space=4.0)

    contact = [c for c in header.get("contact", []) if c]
    if contact:
        joined = "  |  ".join(contact)
        p = _para(doc, space_after=2.0, align=WD_ALIGN_PARAGRAPH.CENTER)
        _run(p, joined, size=cfg["body"] - 0.5)
        _no_proof(p)
        meter.add(joined, cfg["body"], width, space=3.0)

    if cfg["rules"]:
        rule = _para(doc, space_before=2.0, space_after=0.0)
        _bottom_rule(rule, cfg["accent"], size=8)
        meter.pts += 4.0


def _render_role(doc, cfg, role, meter, width, right_tab):
    # Line 1: Company .......... Location
    p = _para(doc, space_before=cfg["space_after"] + 1.0, space_after=0.0,
              keep=True, tab_right=right_tab)
    _run(p, role.get("company", ""), bold=True, size=cfg["body"] + 0.5)
    if role.get("location"):
        _run(p, " \t" +role["location"], size=cfg["body"] - 0.5)
    _no_proof(p)
    meter.add(role.get("company", ""), cfg["body"] + 1, width,
              space=cfg["space_after"] + 1.0)

    # Line 2: Title (| functional role) ........ Dates
    p = _para(doc, space_after=1.0, keep=True, tab_right=right_tab)
    title = role.get("title", "")
    _run(p, title, italic=True)
    if role.get("functional_title"):
        _run(p, "  |  " + role["functional_title"], italic=True,
             size=cfg["body"] - 0.5)
    if role.get("dates"):
        _run(p, " \t" +role["dates"], size=cfg["body"] - 0.5)
    _no_proof(p)
    meter.add(title, cfg["body"], width, space=2.0)

    if role.get("context"):
        p = _para(doc, space_after=cfg["bullet_space"], keep=True)
        _run(p, role["context"], italic=True, size=cfg["body"] - 0.5)
        _no_proof(p)
        meter.add(role["context"], cfg["body"], width, space=cfg["bullet_space"])

    # Plain "Label: value" lines - some roles are written this way rather than
    # as bullets, and forcing a marker onto them would change the structure.
    for line in role.get("lines", []):
        p = _para(doc, space_after=cfg["bullet_space"], indent=0.16)
        for chunk, is_bold in _split_bold(line):
            _run(p, chunk, bold=is_bold)
        _no_proof(p)
        meter.add(line, cfg["body"], width - 0.16, space=cfg["bullet_space"])

    _bullet_list(doc, cfg, role.get("bullets", []), meter, width)

    # Prior titles at the same employer - keeps promotions visible (section 17)
    for sub in role.get("prior_titles", []):
        p = _para(doc, space_before=2.0, space_after=1.0, keep=True,
                  indent=0.16, tab_right=right_tab)
        _run(p, sub.get("title", ""), italic=True, size=cfg["body"] - 0.5)
        if sub.get("dates"):
            _run(p, " \t" +sub["dates"], size=cfg["body"] - 0.5)
        _no_proof(p)
        meter.add(sub.get("title", ""), cfg["body"], width, space=3.0)
        _bullet_list(doc, cfg, sub.get("bullets", []), meter, width, depth=1)


def _render_section(doc, cfg, sec, meter, width, right_tab):
    stype = sec.get("type", "text")
    if sec.get("title"):
        _heading(doc, cfg, sec["title"], meter, width)

    if stype in ("summary", "text"):
        for para in sec.get("paragraphs", []):
            p = _para(doc, space_after=cfg["space_after"])
            for chunk, is_bold in _split_bold(para):
                _run(p, chunk, bold=is_bold)
            _no_proof(p)
            meter.add(para, cfg["body"], width, space=cfg["space_after"])

    elif stype == "skills":
        for g in sec.get("groups", []):
            items = g.get("items", [])
            text = ", ".join(items) if isinstance(items, list) else str(items)
            p = _para(doc, space_after=cfg["bullet_space"])
            _run(p, g.get("label", "") + ":  ", bold=True)
            _run(p, text)
            _no_proof(p)
            meter.add(g.get("label", "") + ":  " + text, cfg["body"], width,
                      space=cfg["bullet_space"])

    elif stype == "experience":
        for role in sec.get("roles", []):
            _render_role(doc, cfg, role, meter, width, right_tab)

    elif stype == "bullets":
        _bullet_list(doc, cfg, sec.get("bullets", []), meter, width)

    elif stype in ("education", "certifications", "entries"):
        for e in sec.get("entries", []):
            p = _para(doc, space_after=cfg["bullet_space"], tab_right=right_tab)
            _run(p, e.get("primary", ""), bold=True)
            if e.get("secondary"):
                _run(p, "  |  " + e["secondary"])
            if e.get("dates"):
                _run(p, " \t" +e["dates"], size=cfg["body"] - 0.5)
            _no_proof(p)
            meter.add(str(e.get("primary", "")) + str(e.get("secondary", "")),
                      cfg["body"], width, space=cfg["bullet_space"])
            if e.get("detail"):
                p = _para(doc, space_after=cfg["bullet_space"], indent=0.16)
                _run(p, e["detail"], size=cfg["body"] - 0.5)
                meter.add(e["detail"], cfg["body"], width, space=2.0)
    else:
        raise ValueError("unknown section type: %r" % stype)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def build(data, out_path, preset=None, margin=None, body=None, quiet=False):
    style = data.get("style", {})
    preset_name = preset or style.get("preset", "recruiter")
    if preset_name not in PRESETS:
        sys.exit("unknown preset %r; choose from %s"
                 % (preset_name, ", ".join(sorted(PRESETS))))
    cfg = dict(PRESETS[preset_name])
    for k in ("font", "body", "name", "heading", "accent", "rules",
              "space_after", "section_before", "bullet_space", "headline_caps"):
        if k in style:
            cfg[k] = style[k]
    if body:
        delta = body - cfg["body"]
        cfg["body"] = body
        cfg["heading"] = round(cfg["heading"] + delta, 2)

    margin_in = margin if margin is not None else style.get("margin_in", 0.7)
    page_w, page_h = 8.5, 11.0
    width = page_w - 2 * margin_in
    right_tab = width

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(page_w)
    sec.page_height = Inches(page_h)
    sec.top_margin = Inches(margin_in)
    sec.bottom_margin = Inches(margin_in)
    sec.left_margin = Inches(margin_in)
    sec.right_margin = Inches(margin_in)
    _set_doc_font(doc, cfg["font"], cfg["body"])

    core = doc.core_properties
    core.title = data.get("meta", {}).get("variant", "Resume")
    core.author = data.get("header", {}).get("name", "")
    core.comments = data.get("meta", {}).get("note", "")

    meter = FillMeter(cfg, page_h, (margin_in, margin_in))
    _render_header(doc, cfg, data.get("header", {}), meter, width)
    for s in data.get("sections", []):
        _render_section(doc, cfg, s, meter, width, right_tab)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    est = meter.pages()
    if not quiet:
        print('wrote %s  [preset=%s font=%s/%.1fpt margin=%.2f"]'
              % (out_path, preset_name, cfg["font"], cfg["body"], margin_in))
        print("estimated length: %.2f pages  (verify in Word - this is a "
              "text-metric estimate, not a layout engine)" % est)
        frac = est - int(est)
        if est > 1.0 and 0.0 < frac < 0.18:
            print("  ! last page is barely used (%.0f%% of a page). Cut content "
                  "or tighten to close the gap." % (frac * 100))
    return est, cfg, margin_in


def build_fit(data, out_path, target, preset=None, quiet=False):
    """Try progressively tighter typography until the estimate fits `target`."""
    ladder = [(0.75, 0), (0.7, 0), (0.7, -0.25), (0.65, -0.25),
              (0.6, -0.5), (0.6, -0.75), (0.55, -1.0)]
    base = PRESETS[preset or data.get("style", {}).get("preset",
                                                       "recruiter")]["body"]
    last = None
    for margin_in, delta in ladder:
        body = round(base + delta, 2) if delta else None
        est, cfg, _ = build(data, out_path, preset=preset, margin=margin_in,
                            body=body, quiet=True)
        last = (est, margin_in, body or base)
        if est <= target + 0.02:
            if not quiet:
                print('wrote %s  [fit=%g pages: margin=%.2f" body=%.2fpt '
                      "-> est %.2f pages]"
                      % (out_path, target, margin_in, body or base, est))
            return est
    est, margin_in, body = last
    if not quiet:
        print('wrote %s  [could NOT reach %g pages by typography alone: '
              'tightest setting margin=%.2f" body=%.2fpt still estimates '
              "%.2f pages]" % (out_path, target, margin_in, body, est))
        print("  -> cut content instead. Typography past this point looks "
              "cramped and reads as desperate.")
    return est


# --------------------------------------------------------------------------
# plain-text and markdown renderings
# --------------------------------------------------------------------------
def _plain(text):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))


def _btext(b):
    return _plain(b["text"] if isinstance(b, dict) else b)


def _flatten(bullets, depth=0, marker="- ", strip_bold=True):
    """Flatten nested bullets into indented lines for the txt/md renderings.
    Dropping `children` here would silently lose content from the ATS copy."""
    out = []
    for b in bullets:
        if isinstance(b, dict):
            text, children = b.get("text", ""), b.get("children") or []
        else:
            text, children = str(b), []
        out.append("  " * depth + marker + (_plain(text) if strip_bold else text))
        if children:
            out += _flatten(children, depth + 1, marker, strip_bold)
    return out


def render_txt(data):
    """Plain-text ATS rendering - safe to paste into a web form. No tabs, no
    box glyphs, no bullet characters that mangle in a textarea."""
    out, h = [], data.get("header", {})
    out.append(h.get("name", ""))
    if h.get("headline"):
        out.append(_plain(h["headline"]))
    if h.get("contact"):
        out.append(" | ".join(h["contact"]))
    for s in data.get("sections", []):
        out.append("")
        if s.get("title"):
            out.append(s["title"].upper())
            out.append("-" * len(s["title"]))
        t = s.get("type", "text")
        if t in ("summary", "text"):
            out += [_plain(p) for p in s.get("paragraphs", [])]
        elif t == "skills":
            for g in s.get("groups", []):
                items = g.get("items", [])
                joined = ", ".join(items) if isinstance(items, list) else items
                out.append("%s: %s" % (g.get("label", ""), joined))
        elif t == "experience":
            for r in s.get("roles", []):
                out.append("")
                out.append(", ".join(
                    x for x in (r.get("company"), r.get("location")) if x))
                line = r.get("title", "")
                if r.get("functional_title"):
                    line += " | " + r["functional_title"]
                out.append("%s (%s)" % (line, r.get("dates", "")))
                if r.get("context"):
                    out.append(_plain(r["context"]))
                out += [_plain(l) for l in r.get("lines", [])]
                out += _flatten(r.get("bullets", []))
                for sub in r.get("prior_titles", []):
                    out.append("%s (%s)" % (sub.get("title", ""),
                                            sub.get("dates", "")))
                    out += _flatten(sub.get("bullets", []), depth=1)
        elif t == "bullets":
            out += _flatten(s.get("bullets", []))
        else:
            for e in s.get("entries", []):
                bits = [x for x in (e.get("primary"), e.get("secondary"),
                                    e.get("dates")) if x]
                out.append(" | ".join(bits))
                if e.get("detail"):
                    out.append("  " + _plain(e["detail"]))
    return "\n".join(out).rstrip() + "\n"


def render_md(data):
    out, h = [], data.get("header", {})
    out.append("# " + h.get("name", ""))
    if h.get("headline"):
        out.append("**%s**" % h["headline"])
    if h.get("contact"):
        out.append(" - ".join(h["contact"]))
    for s in data.get("sections", []):
        out.append("")
        if s.get("title"):
            out.append("## " + s["title"])
        t = s.get("type", "text")
        if t in ("summary", "text"):
            out += s.get("paragraphs", [])
        elif t == "skills":
            for g in s.get("groups", []):
                items = g.get("items", [])
                joined = ", ".join(items) if isinstance(items, list) else items
                out.append("**%s:** %s" % (g.get("label", ""), joined))
        elif t == "experience":
            for r in s.get("roles", []):
                out.append("")
                out.append("### %s - %s" % (r.get("title", ""),
                                            r.get("company", "")))
                out.append("*%s | %s*" % (r.get("location", ""),
                                          r.get("dates", "")))
                if r.get("context"):
                    out.append(r["context"])
                out += list(r.get("lines", []))
                out += _flatten(r.get("bullets", []), strip_bold=False)
                for sub in r.get("prior_titles", []):
                    out.append("")
                    out.append("**%s** *(%s)*" % (sub.get("title", ""),
                                                  sub.get("dates", "")))
                    out += _flatten(sub.get("bullets", []), depth=1, strip_bold=False)
        elif t == "bullets":
            out += _flatten(s.get("bullets", []), strip_bold=False)
        else:
            for e in s.get("entries", []):
                bits = [x for x in (e.get("primary"), e.get("secondary"),
                                    e.get("dates")) if x]
                out.append("- " + " | ".join(bits))
    return "\n".join(out).rstrip() + "\n"


SCHEMA = """
sresume JSON input
==================
{
  "meta":   {"variant": "Principal Architect", "note": "for Acme req 1234"},
  "style":  {"preset": "recruiter", "margin_in": 0.7},   // every field optional
  "header": {
    "name": "FIRST LAST",
    "headline": "Principal Architect | Cloud, Distributed Systems, Enterprise AI",
    "contact": ["Plano, TX", "555-555-5555", "me@example.com",
                "linkedin.com/in/handle"]
  },
  "sections": [
    {"type":"summary", "title":"Professional Summary",
     "paragraphs":["..."]},

    {"type":"skills", "title":"Technical Skills",
     "groups":[{"label":"Cloud & Platform", "items":["AWS","Kubernetes"]}]},

    {"type":"experience", "title":"Professional Experience",
     "roles":[{
        "company":"Acme Bank", "location":"Plano, TX",
        "title":"Principal Engineer",
        "functional_title":"Platform Architect",     // optional, section 26
        "dates":"2019 - Present",
        "context":"one italic line of scope/scale",  // optional
        "bullets":["Designed ... **Kafka** ..."],    // **bold** supported
        "prior_titles":[{"title":"Senior Engineer","dates":"2015 - 2019",
                         "bullets":["..."]}]         // promotions, section 17
     }]},

    {"type":"bullets", "title":"Selected Accomplishments", "bullets":["..."]},

    {"type":"education", "title":"Education",
     "entries":[{"primary":"B.S. Computer Science","secondary":"University",
                 "dates":"1993","detail":"optional second line"}]},

    {"type":"certifications", "title":"Certifications", "entries":[...]},
    {"type":"text", "title":"Anything Else", "paragraphs":["..."]}
  ]
}

presets: """ + ", ".join(sorted(PRESETS)) + """
Sections render in the order given. Omit "title" to render a section untitled.
"""


def main():
    ap = argparse.ArgumentParser(description="Build an ATS-safe .docx resume.")
    ap.add_argument("input", nargs="?", help="resume JSON file")
    ap.add_argument("-o", "--out", help="output .docx path")
    ap.add_argument("--preset", choices=sorted(PRESETS),
                    help="typography preset (overrides style.preset)")
    ap.add_argument("--margin", type=float, help="page margin in inches")
    ap.add_argument("--body", type=float, help="body font size in points")
    ap.add_argument("--fit", type=float, metavar="PAGES",
                    help="auto-tighten typography to reach this page count")
    ap.add_argument("--txt", help="also write a plain-text ATS version here")
    ap.add_argument("--md", help="also write a markdown version here")
    ap.add_argument("--schema", action="store_true", help="print input schema")
    a = ap.parse_args()

    if a.schema:
        print(SCHEMA)
        return
    if not a.input:
        ap.error("input JSON required (or use --schema)")

    data = json.loads(Path(a.input).read_text(encoding="utf-8"))

    if a.out:
        if a.fit:
            build_fit(data, a.out, a.fit, preset=a.preset)
        else:
            build(data, a.out, preset=a.preset, margin=a.margin, body=a.body)
    if a.txt:
        Path(a.txt).write_text(render_txt(data), encoding="utf-8")
        print("wrote %s" % a.txt)
    if a.md:
        Path(a.md).write_text(render_md(data), encoding="utf-8")
        print("wrote %s" % a.md)
    if not (a.out or a.txt or a.md):
        ap.error("nothing to do: pass -o, --txt or --md")


if __name__ == "__main__":
    main()
