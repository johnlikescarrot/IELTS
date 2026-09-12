#!/usr/bin/env python3
"""Render the IELTS Master Course book (Markdown sources) into a styled PDF.
Usage: python3 book/build_pdf.py  ->  IELTS-Master-Course-Book.pdf
Markup subset: #/##/### headings, paragraphs with **bold** *italic* `code`,
- bullets, 1. numbered lists, | tables |, > TIP boxes, ! WARNING boxes,
>>> EXAMPLE boxes (multi-line until blank line + non->>> line), --- rule.
"""
import re, os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, ListFlowable, ListItem, HRFlowable,
    PageBreak, KeepTogether, Image, Flowable, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics

ROOT = os.path.dirname(os.path.abspath(__file__))
CHAPTERS = [
    ("01_test_overview.md", "Part A — The Test"),
    ("02_study_plans.md", "Part A — The Test"),
    ("03_listening_mastery.md", "Part B — Listening"),
    ("04_listening_types.md", "Part B — Listening"),
    ("05_listening_practice.md", "Part B — Listening"),
    ("06_reading_mastery.md", "Part C — Reading"),
    ("07_reading_types.md", "Part C — Reading"),
    ("08_reading_practice.md", "Part C — Reading"),
    ("09_speaking_mastery.md", "Part D — Speaking"),
    ("10_speaking_bank.md", "Part D — Speaking"),
    ("11_writing_scoring.md", "Part E — Writing"),
    ("12_writing_task1.md", "Part E — Writing"),
    ("13_writing_task2.md", "Part E — Writing"),
    ("14_language_examday.md", "Part F — Language & Exam Day"),
    ("15_answers_keys.md", "Part G — Answers & Trackers"),
]

NAVY = colors.HexColor("#1F3864")
RED = colors.HexColor("#C00000")
TEAL = colors.HexColor("#0E6B6B")
GOLD = colors.HexColor("#BF9000")
LIGHT_BG = colors.HexColor("#F2F4F8")
TIP_BG = colors.HexColor("#EAF4EA")
TIP_BD = colors.HexColor("#2E7D32")
WARN_BG = colors.HexColor("#FDECEA")
WARN_BD = colors.HexColor("#C00000")
EX_BG = colors.HexColor("#EEF3FB")
EX_BD = colors.HexColor("#1F3864")

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', t)
    return t

def make_styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=ss["Normal"], fontName="Helvetica",
        fontSize=10, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=5,
        textColor=colors.HexColor("#222222"))
    h1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=NAVY, spaceBefore=0, spaceAfter=10,
        keepWithNext=True, outlineLevel=0)
    h2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
        fontSize=14.5, leading=18, textColor=RED, spaceBefore=12, spaceAfter=6,
        keepWithNext=True, outlineLevel=1)
    h3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=4,
        keepWithNext=True, outlineLevel=2)
    bullet = ParagraphStyle("Bullet", parent=body, alignment=TA_LEFT,
        leftIndent=14, firstLineIndent=0, spaceAfter=3)
    tip = ParagraphStyle("Tip", parent=body, alignment=TA_LEFT, fontSize=9.5,
        leading=13.5, spaceAfter=2)
    cell = ParagraphStyle("Cell", parent=body, alignment=TA_LEFT, fontSize=9,
        leading=12, spaceAfter=2)
    cellH = ParagraphStyle("CellH", parent=cell, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER)
    cap = ParagraphStyle("Cap", parent=body, alignment=TA_CENTER, fontSize=9,
        textColor=colors.HexColor("#555555"), spaceBefore=2, spaceAfter=8)
    return dict(body=body, h1=h1, h2=h2, h3=h3, bullet=bullet, tip=tip,
                cell=cell, cellH=cellH, cap=cap)

ST = make_styles()

def p(text, style=None):
    return Paragraph(inline(text), style or ST["body"])

def box(lines, kind):
    bg, bd, label = {"tip": (TIP_BG, TIP_BD, "TIP"),
                     "warn": (WARN_BG, WARN_BD, "WARNING"),
                     "ex": (EX_BG, EX_BD, "EXAMPLE")}[kind]
    inner = [Paragraph(f"<b>{label}.</b> " + inline(lines[0]), ST["tip"])]
    for ln in lines[1:]:
        inner.append(Paragraph(inline(ln), ST["tip"]))
    t = Table([[inner]], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1.2, bd),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 5)])

def md_table(rows):
    cells = [[ln.strip().strip("|").split("|") for ln in rows]]
    data = [[c.strip() for c in r] for r in cells[0]]
    ncols = max(len(r) for r in data)
    data = [r + [""] * (ncols - len(r)) for r in data]
    style = ST["cellH"]
    body = []
    for i, r in enumerate(data):
        if i == 0:
            body.append([Paragraph("<b>" + inline(c) + "</b>", ST["cellH"]) for c in r])
        else:
            body.append([Paragraph(inline(c), ST["cell"]) for c in r])
    W = 170*mm
    widths = [W / ncols] * ncols
    # widen first col if it looks like a label column
    if ncols == 2:
        widths = [W*0.32, W*0.68]
    t = Table(body, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#9AA3B2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [Spacer(1, 3), t, Spacer(1, 6)]

def parse_md(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    story = []
    i, n = 0, len(lines)
    list_buf, list_kind = [], None
    def flush_list():
        nonlocal list_buf, list_kind
        if not list_buf:
            return
        items = [ListItem(Paragraph(inline(x), ST["bullet"]),
                          leftIndent=14, bulletColor=NAVY) for x in list_buf]
        story.append(ListFlowable(items,
            bulletType="1" if list_kind == "num" else "bullet",
            bulletFontName="Helvetica-Bold", bulletFontSize=10,
            leftIndent=14, bulletOffset=0, spaceBefore=2, spaceAfter=6))
        list_buf, list_kind = [], None
    while i < n:
        ln = lines[i].rstrip()
        if not ln.strip():
            flush_list(); i += 1; continue
        if ln.startswith("|"):
            flush_list()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                r = lines[i].strip()
                if not re.match(r"^\|[\s\-\:|]+\|$", r):
                    rows.append(r)
                i += 1
            story.extend(md_table(rows)); continue
        if ln.startswith(">>>"):
            flush_list()
            buf = [ln[3:].strip()]
            i += 1
            while i < n and lines[i].strip().startswith(">>>"):
                buf.append(lines[i].strip()[3:].strip()); i += 1
            story.append(box(buf, "ex")); continue
        if ln.startswith(">"):
            flush_list()
            buf = [ln[1:].strip()]
            i += 1
            while i < n and lines[i].strip().startswith(">") and not lines[i].strip().startswith(">>>"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            story.append(box(buf, "tip")); continue
        if ln.startswith("!"):
            flush_list()
            buf = [ln[1:].strip()]
            i += 1
            while i < n and lines[i].strip().startswith("!"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            story.append(box(buf, "warn")); continue
        if ln.startswith("---"):
            flush_list()
            story.append(HRFlowable(width="100%", thickness=1, color=NAVY,
                                    spaceBefore=6, spaceAfter=8)); i += 1; continue
        if ln.startswith("# "):
            flush_list(); story.append(PageBreak())
            story.append(Paragraph(inline(ln[2:]), ST["h1"])); i += 1; continue
        if ln.startswith("## "):
            flush_list(); story.append(Paragraph(inline(ln[3:]), ST["h2"])); i += 1; continue
        if ln.startswith("### "):
            flush_list(); story.append(Paragraph(inline(ln[4:]), ST["h3"])); i += 1; continue
        m = re.match(r"^(\d+)\.\s+(.*)", ln)
        if m:
            if list_kind != "num":
                flush_list(); list_kind = "num"
            list_buf.append(m.group(2)); i += 1; continue
        if re.match(r"^[-*]\s+", ln):
            if list_kind != "bul":
                flush_list(); list_kind = "bul"
            list_buf.append(re.sub(r"^[-*]\s+", "", ln)); i += 1; continue
        flush_list()
        para = [ln]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#{1,3}\s|\||>>>|>|!|---|[-*]\s|\d+\.\s)", lines[i].strip()):
            para.append(lines[i].strip()); i += 1
        story.append(p(" ".join(para)))
    flush_list()
    return story

def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(15*mm, 12*mm, "IELTS Master Course — The Complete Preparation Book")
        canvas.drawRightString(195*mm, 12*mm, f"{doc.page}")
        canvas.setStrokeColor(NAVY); canvas.setLineWidth(0.8)
        canvas.line(15*mm, 14.5*mm, 195*mm, 14.5*mm)
        part = getattr(doc, "_part_now", "")
        if part:
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColor(NAVY)
            canvas.drawRightString(195*mm, 283*mm, part)
    canvas.restoreState()

def make_after_flowable(doc):
    def after_flowable(flowable):
        if isinstance(flowable, Paragraph):
            if flowable.style.name == "H1":
                doc._part_now = doc._chap_part.get(flowable.getPlainText().strip(), "")
            lvl = getattr(flowable.style, "outlineLevel", None)
            if lvl is not None:
                doc.notify("TOCEntry", (lvl, flowable.getPlainText().strip(), doc.page))
    return after_flowable

def build_cover(path):
    from reportlab.pdfgen.canvas import Canvas
    c = Canvas(path, pagesize=A4)
    W, H = A4
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(RED); c.rect(0, H-52*mm, W, 52*mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W/2, H-22*mm, "THE COMPLETE 12-HOUR VIDEO COURSE — IN BOOK FORM")
    c.setFont("Helvetica-Bold", 46)
    c.drawCentredString(W/2, H-95*mm, "IELTS")
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H-112*mm, "MASTER COURSE")
    c.setFont("Helvetica", 16)
    c.setFillColor(GOLD)
    c.drawCentredString(W/2, H-128*mm, "Listening  •  Reading  •  Writing  •  Speaking")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 13)
    lines = ["The Most Comprehensive IELTS Preparation Book Ever Created",
             "From Beginner Foundations to Band 7+ Mastery",
             "",
             "15 Chapters  •  4 Full Modules  •  100s of Worked Examples",
             "Practice Tests  •  Model Essays & Reports  •  Speaking Bank",
             "Study Plans  •  Vocabulary & Grammar  •  Answer Keys"]
    y = H-160*mm
    for ln in lines:
        c.drawCentredString(W/2, y, ln); y -= 9*mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#B0B8C8"))
    c.drawCentredString(W/2, 38*mm, "Compiled from the 12-part IELTS Master-Course video series (Beginners 2023)")
    c.drawCentredString(W/2, 31*mm, "Academic + General Training  •  Paper & Computer-Delivered")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.white)
    c.drawCentredString(W/2, 22*mm, "2026 Edition")
    c.showPage(); c.save()

def build():
    out = os.path.join(os.path.dirname(ROOT), "IELTS-Master-Course-Book.pdf")
    main_pdf = os.path.join(ROOT, "_main.pdf")
    cover_pdf = os.path.join(ROOT, "_cover.pdf")
    doc = BaseDocTemplate(main_pdf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                          topMargin=18*mm, bottomMargin=18*mm,
                          title="IELTS Master Course — Complete Preparation Book",
                          author="IELTS Master Course")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=header_footer)])
    doc._chap_part = {}
    for fname, part in CHAPTERS:
        with open(os.path.join(ROOT, fname), encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    doc._chap_part[line[2:].strip()] = part
                    break
    doc.afterFlowable = make_after_flowable(doc)
    doc._part_now = ""
    story = []
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("toc0", fontName="Helvetica-Bold", fontSize=12, leading=16,
                       textColor=NAVY, spaceBefore=4),
        ParagraphStyle("toc1", fontName="Helvetica", fontSize=10, leading=14,
                       leftIndent=14, textColor=colors.HexColor("#333333")),
        ParagraphStyle("toc2", fontName="Helvetica-Oblique", fontSize=9, leading=12,
                       leftIndent=28, textColor=colors.HexColor("#555555")),
    ]
    story.append(Paragraph("Contents", ST["h1"]))
    story.append(toc); story.append(PageBreak())
    for fname, part in CHAPTERS:
        story.extend(parse_md(os.path.join(ROOT, fname)))
    doc.multiBuild(story)
    build_cover(cover_pdf)
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    for pdf in (cover_pdf, main_pdf):
        r = PdfReader(pdf)
        for pg in r.pages:
            w.add_page(pg)
    with open(out, "wb") as f:
        w.write(f)
    os.remove(cover_pdf); os.remove(main_pdf)
    print("BUILT:", out, os.path.getsize(out), "bytes")

if __name__ == "__main__":
    build()
