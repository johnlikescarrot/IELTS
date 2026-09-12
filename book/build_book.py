#!/usr/bin/env python3
"""Build the IELTS Master Guide PDF from lightweight-markup content files.

Markup grammar (line-based):
  # Title            -> chapter heading (H1), page-break before
  ## Title           -> section heading (H2)
  ### Title          -> sub-section heading (H3)
  #### Title         -> sub-sub heading (H4)
  - item             -> bullet
  + item             -> numbered item (auto-numbered per group)
  > TEXT             -> callout/tip box (TEXT may start with LABEL: )
  <<<                -> open an example/model-answer box
  >>>                -> close the box
  [[table:Caption]]  -> open a table (caption optional)
  | a | b | c |      -> table row (first row = header if after [[table)
  ]]                 -> close table
  ---                -> horizontal rule
  blank line         -> paragraph break
Inline markup: **bold**, *italic*.

Content files are read from CONTENT_DIR in filename order.
"""
import os
import re
import glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, Table, TableStyle, HRFlowable,
                                KeepTogether, NextPageTemplate, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas as canvas_module

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE, "content")
OUT_PDF = os.path.join(BASE, "IELTS_Master_Guide.pdf")

# ---------------------------------------------------------------- palette
NAVY   = colors.HexColor("#12314E")
NAVY2  = colors.HexColor("#1B4A78")
GOLD   = colors.HexColor("#C9A227")
GOLD2  = colors.HexColor("#8C6D12")
TEAL   = colors.HexColor("#1F7A8C")
TEALBG = colors.HexColor("#EAF4F6")
GOLDBG = colors.HexColor("#FBF3E0")
GREYBG = colors.HexColor("#F3F5F7")
INK    = colors.HexColor("#1E2A35")
MUTE   = colors.HexColor("#5A6672")
LINE   = colors.HexColor("#D8DEE5")
EXBG   = colors.HexColor("#EFF3F7")
WHITE  = colors.white

BOOK_TITLE = "IELTS Master Guide"
BOOK_SUBTITLE = ("The Complete Preparation Book \u2014 Listening \u00b7 Reading \u00b7 Writing \u00b7 Speaking")

# ---------------------------------------------------------------- styles
def P(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.6, leading=14.2, textColor=INK,
                alignment=TA_JUSTIFY, spaceAfter=5, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

STYLES = {
    "H1": P("H1", fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=NAVY,
            alignment=TA_LEFT, spaceBefore=0, spaceAfter=10),
    "H2": P("H2", fontName="Helvetica-Bold", fontSize=14.5, leading=18, textColor=NAVY2,
            alignment=TA_LEFT, spaceBefore=13, spaceAfter=6),
    "H3": P("H3", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=TEAL,
            alignment=TA_LEFT, spaceBefore=9, spaceAfter=4),
    "H4": P("H4", fontName="Helvetica-Bold", fontSize=10.2, leading=13, textColor=INK,
            alignment=TA_LEFT, spaceBefore=7, spaceAfter=3),
    "body": P("body"),
    "bullet": P("bullet", leftIndent=14, bulletIndent=4, spaceAfter=3.5),
    "number": P("number", leftIndent=14, spaceAfter=3.5),
    "tip": P("tip", backColor=TEALBG, borderColor=TEAL, borderWidth=0.8,
             borderPadding=7, leftIndent=2, rightIndent=2, spaceBefore=6, spaceAfter=8,
             fontSize=9.4, leading=13.6),
    "warn": P("warn", backColor=GOLDBG, borderColor=GOLD2, borderWidth=0.8,
              borderPadding=7, leftIndent=2, rightIndent=2, spaceBefore=6, spaceAfter=8,
              fontSize=9.4, leading=13.6),
    "exbody": P("exbody", fontSize=9.2, leading=13.6, spaceAfter=2),
    "exbox": P("exbox", backColor=EXBG, borderColor=NAVY2, borderWidth=0.8,
               borderPadding=8, leftIndent=2, rightIndent=2, spaceBefore=6, spaceAfter=8,
               fontSize=9.2, leading=13.4),
    "tblcap": P("tblcap", fontName="Helvetica-Bold", fontSize=9.4, textColor=NAVY2,
                spaceBefore=7, spaceAfter=3),
    "tcell": P("tcell", fontSize=8.6, leading=10.8, textColor=INK,
               alignment=TA_LEFT, spaceAfter=0),
    "tcellh": P("tcellh", fontName="Helvetica-Bold", fontSize=8.6, leading=10.8,
                textColor=WHITE, alignment=TA_LEFT, spaceAfter=0),
    "tocc": P("tocc", fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=NAVY,
              alignment=TA_LEFT, spaceAfter=10),
    "center": P("center", alignment=TA_CENTER, fontSize=10.5, leading=15, spaceAfter=6),
    "centertitle": P("centertitle", fontName="Helvetica-Bold", fontSize=24, leading=29,
                     textColor=NAVY, alignment=TA_CENTER, spaceAfter=10),
    "centersub": P("centersub", fontName="Helvetica", fontSize=12, leading=17,
                   textColor=MUTE, alignment=TA_CENTER, spaceAfter=8),
}

INLINE_RE = re.compile(r"(\*\*.+?\*\*|\*.+?\*)")

def rich(text, style_name="body"):
    """Convert **bold** and *italic* inline markup into <b>/<i> tags."""
    out = []
    for tok in INLINE_RE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            out.append("<b>%s</b>" % tok[2:-2])
        elif tok.startswith("*") and tok.endswith("*"):
            out.append("<i>%s</i>" % tok[1:-1])
        else:
            out.append(tok.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(out)

# ---------------------------------------------------------------- flowables
class ExampleBox(Flowable):
    """A shaded, bordered box containing model answers / examples (multi-paragraph)."""
    def __init__(self, items, width):
        Flowable.__init__(self)
        self.items = items
        self.width = width
        self.pad = 8
        self.inner = width - 2 * self.pad
        self.height = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.inner = availWidth - 2 * self.pad
        h = 2 * self.pad
        for it in self.items:
            _, ih = it.wrap(self.inner, availHeight)
            h += ih + (2 if it is not self.items[-1] else 0)
        self.height = h
        return (availWidth, h)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(EXBG)
        c.setStrokeColor(NAVY2)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.width, self.height, 3, stroke=1, fill=1)
        y = self.height - self.pad
        for it in self.items:
            _, ih = it.wrap(self.inner, 1000)
            y -= ih
            it.drawOn(c, self.pad, y)
            y -= 2
        c.restoreState()

# ---------------------------------------------------------------- doc template
class BookTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        self._cur_chapter = ""
        self._page_chapters = {}       # page -> chapter, collected during the current pass
        self._last_page_chapters = {}  # page -> chapter, from the previous multiBuild pass
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="main",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                            onPage=self._header_footer)])

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            if flowable.style.name == "H1":
                self._cur_chapter = flowable.getPlainText()
                self._page_chapters[self.page] = self._cur_chapter
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
            elif flowable.style.name == "H2":
                self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))

    def _header_footer(self, canv, doc):
        canv.saveState()
        w, h = A4
        if doc.page == 1:
            # a new pass is starting: promote this pass's page->chapter map
            self._last_page_chapters = self._page_chapters
            self._page_chapters = {}
            self._cur_chapter = ""
            self._cover(canv, doc)
            canv.restoreState()
            return
        # header
        if doc.page > 1:
            canv.setStrokeColor(LINE)
            canv.setLineWidth(0.6)
            canv.line(self.leftMargin, h - 18*mm, w - self.rightMargin, h - 18*mm)
            canv.setFont("Helvetica", 7.6)
            canv.setFillColor(MUTE)
            canv.drawString(self.leftMargin, h - 16*mm, BOOK_TITLE.upper())
            chapter = self._last_page_chapters.get(doc.page, "")
            if chapter:
                canv.setFillColor(NAVY2)
                canv.setFont("Helvetica-Bold", 7.8)
                canv.drawRightString(w - self.rightMargin, h - 16*mm,
                                     chapter.upper())
            # footer
            canv.setStrokeColor(LINE)
            canv.line(self.leftMargin, 15*mm, w - self.rightMargin, 15*mm)
            canv.setFont("Helvetica", 8)
            canv.setFillColor(MUTE)
            canv.drawString(self.leftMargin, 11.5*mm,
                            "Compiled from the IELTS 12-Hour Full Course (2023)")
            canv.setFont("Helvetica-Bold", 9)
            canv.setFillColor(NAVY)
            canv.drawRightString(w - self.rightMargin, 11.5*mm, str(doc.page))
        canv.restoreState()

    def _cover(self, canv, doc):
        canv.saveState()
        w, h = A4
        canv.setFillColor(NAVY)
        canv.rect(0, 0, w, h, stroke=0, fill=1)
        # accent band
        canv.setFillColor(GOLD)
        canv.rect(0, h*0.32, w, 3.2*mm, stroke=0, fill=1)
        # eyebrow
        canv.setFont("Helvetica-Bold", 12)
        canv.setFillColor(GOLD)
        canv.drawCentredString(w/2, h*0.80, "T H E   C O M P L E T E   P R E P A R A T I O N   B O O K")
        # title
        canv.setFont("Helvetica-Bold", 52)
        canv.setFillColor(WHITE)
        canv.drawCentredString(w/2, h*0.66, "IELTS")
        canv.setFont("Helvetica-Bold", 40)
        canv.setFillColor(GOLD)
        canv.drawCentredString(w/2, h*0.585, "Master Guide")
        # subtitle
        canv.setFont("Helvetica", 14)
        canv.setFillColor(colors.HexColor("#D7E3EE"))
        canv.drawCentredString(w/2, h*0.50, "Listening  \u00b7  Reading  \u00b7  Writing  \u00b7  Speaking")
        canv.setFont("Helvetica", 12.5)
        canv.drawCentredString(w/2, h*0.465, "Strategies \u00b7 Techniques \u00b7 Model Answers \u00b7 Vocabulary \u00b7 Band Scores")
        # bottom meta
        canv.setFont("Helvetica", 11)
        canv.setFillColor(colors.HexColor("#9FB6C9"))
        canv.drawCentredString(w/2, h*0.26,
            "A comprehensive guide compiled from a complete study of the")
        canv.drawCentredString(w/2, h*0.235,
            "\u201cIELTS 12 Hours Full Course for Beginners 2023 \u2014 Master-Course of 4 Components\u201d")
        canv.setFont("Helvetica-Bold", 11)
        canv.setFillColor(GOLD)
        canv.drawCentredString(w/2, h*0.155, "Academic  &  General Training")
        canv.restoreState()

# ---------------------------------------------------------------- parser
def parse_file(path, story):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    number_state = [0]  # mutable counter for numbered groups
    bullets = []        # list of Paragraphs for a bullet group
    numbered = []       # list of Paragraphs for a numbered group
    ex_items = []       # list for example box
    table_rows = []
    table_caption = None
    in_table = False
    in_ex = False

    def flush_bullets():
        if bullets:
            story.append(Paragraph("\n".join(bullets), STYLES["bullet"]))
            bullets.clear()

    def flush_numbered():
        if numbered:
            story.append(Paragraph("\n".join(numbered), STYLES["number"]))
            numbered.clear()

    def flush_table():
        nonlocal table_caption, table_rows
        if not in_table:
            return
        if table_caption:
            story.append(Paragraph(table_caption, STYLES["tblcap"]))
        if table_rows:
            def _esc(s):
                return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            def _cell(s, header=False):
                txt = _esc(s.replace("**", "").replace("*", "").strip())
                return Paragraph(txt, STYLES["tcellh"] if header else STYLES["tcell"])
            data = [[_cell(c, header=(ri == 0)) for c in r] for ri, r in enumerate(table_rows)]
            ncols = max(len(r) for r in data)
            avail = A4[0] - 44*mm
            colw = [avail / ncols] * ncols
            t = Table(data, colWidths=colw, hAlign="LEFT", repeatRows=1)
            style = [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREYBG]),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
            t.setStyle(TableStyle(style))
            story.append(t)
            story.append(Spacer(1, 6))
        table_rows = []
        table_caption = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if in_ex:
            if stripped == ">>>":
                story.append(ExampleBox(ex_items, 0))
                ex_items = []
                in_ex = False
                continue
            if stripped == "":
                if ex_items:
                    ex_items.append(Spacer(1, 3))
                continue
            ex_items.append(Paragraph(rich(stripped, "exbody"), STYLES["exbody"]))
            continue

        if in_table:
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                table_rows.append(cells)
                continue
            # any non-row line (blank, heading, paragraph, "]]") closes the table
            flush_table()
            in_table = False
            if stripped == "]]":
                continue

        if stripped.startswith("[[table"):
            flush_bullets(); flush_numbered()
            m = re.match(r"\[\[table\s*:?\s*(.*)\]\]", stripped)
            table_caption = m.group(1).strip() if m and m.group(1) else None
            in_table = True
            table_rows = []
            continue

        if stripped == "<<<":
            flush_bullets(); flush_numbered()
            in_ex = True
            ex_items = []
            continue

        if stripped.startswith("# "):
            flush_bullets(); flush_numbered(); flush_table()
            story.append(NextPageTemplate("main"))
            story.append(PageBreak())
            story.append(Paragraph(rich(stripped[2:]), STYLES["H1"]))
            continue
        if stripped.startswith("## "):
            flush_bullets(); flush_numbered()
            story.append(Paragraph(rich(stripped[3:]), STYLES["H2"]))
            continue
        if stripped.startswith("### "):
            flush_bullets(); flush_numbered()
            story.append(Paragraph(rich(stripped[4:]), STYLES["H3"]))
            continue
        if stripped.startswith("#### "):
            flush_bullets(); flush_numbered()
            story.append(Paragraph(rich(stripped[5:]), STYLES["H4"]))
            continue

        if stripped == "---":
            flush_bullets(); flush_numbered()
            story.append(Spacer(1, 2))
            story.append(HRFlowable(width="100%", thickness=0.6, color=LINE))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("- "):
            flush_numbered()
            bullets.append("&bull;&nbsp;" + rich(stripped[2:]))
            continue

        if stripped.startswith("+ "):
            flush_bullets()
            number_state[0] += 1
            numbered.append("<b>%d.</b>&nbsp;&nbsp;" % number_state[0] + rich(stripped[2:]))
            continue

        if stripped.startswith(">"):
            flush_bullets(); flush_numbered()
            body = stripped[1:].strip()
            style = "tip"
            if re.match(r"^(TIP|NOTE|REMEMBER|IMPORTANT)\b", body, re.I):
                style = "tip"
                body = re.sub(r"^(TIP|NOTE|REMEMBER|IMPORTANT):?\s*", "", body, flags=re.I)
            elif re.match(r"^(WARNING|WARN|BEWARE|DANGER)\b", body, re.I):
                style = "warn"
                body = re.sub(r"^(WARNING|WARN|BEWARE|DANGER):?\s*", "", body, flags=re.I)
            story.append(Paragraph(rich(body, style), STYLES[style]))
            continue

        if stripped.startswith("%%"):
            flush_bullets(); flush_numbered()
            story.append(Paragraph(rich(stripped[2:].strip()), STYLES["centertitle"]))
            continue
        if stripped.startswith("% "):
            flush_bullets(); flush_numbered()
            story.append(Paragraph(rich(stripped[2:].strip()), STYLES["center"]))
            continue

        if stripped == "":
            flush_bullets(); flush_numbered()
            number_state[0] = 0
            continue

        # ordinary paragraph
        flush_bullets(); flush_numbered()
        story.append(Paragraph(rich(stripped), STYLES["body"]))

    flush_bullets(); flush_numbered(); flush_table()

# ---------------------------------------------------------------- main
def build():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "*.txt")))
    if not files:
        raise SystemExit("No content files found in %s" % CONTENT_DIR)

    doc = BookTemplate(OUT_PDF, pagesize=A4,
                       leftMargin=20*mm, rightMargin=20*mm,
                       topMargin=22*mm, bottomMargin=20*mm,
                       title=BOOK_TITLE + " \u2014 " + BOOK_SUBTITLE,
                       author="IELTS Master Guide")

    # --- front matter story
    story = []
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("toc1", fontName="Helvetica-Bold", fontSize=10.5, leading=15,
                       textColor=NAVY, leftIndent=0, spaceBefore=3),
        ParagraphStyle("toc2", fontName="Helvetica", fontSize=9.4, leading=13.5,
                       textColor=INK, leftIndent=14, spaceBefore=1.5),
        ParagraphStyle("toc3", fontName="Helvetica", fontSize=8.6, leading=12.5,
                       textColor=MUTE, leftIndent=28, spaceBefore=1),
    ]

    for f in files:
        parse_file(f, story)

    # The front-matter file supplies: title page, about, TOC placeholder, how-to-use.
    # TOC is injected by a placeholder sentinel in 00_front.txt: a paragraph '[[[TOC]]]'.
    injected = False
    final_story = []
    for flow in story:
        if isinstance(flow, Paragraph) and flow.getPlainText().strip() == "[[[TOC]]]":
            final_story.append(PageBreak())
            final_story.append(Paragraph("Contents", STYLES["tocc"]))
            final_story.append(toc)
            injected = True
        else:
            final_story.append(flow)

    doc.multiBuild(final_story)
    print("PDF written:", OUT_PDF, "(", os.path.getsize(OUT_PDF)//1024, "KB )")
    if not injected:
        print("NOTE: no [[[TOC]]] placeholder found; TOC not inserted.")

if __name__ == "__main__":
    build()
