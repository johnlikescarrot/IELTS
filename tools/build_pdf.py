#!/usr/bin/env python3
"""Build the IELTS Masterclass PDF from the markdown sources in book/."""
import os, re, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, Table, TableStyle, KeepTogether,
                                ListFlowable, ListItem, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

NAVY = colors.HexColor("#12314f")
ACCENT = colors.HexColor("#b5651d")
LIGHT = colors.HexColor("#eef3f8")
RULE = colors.HexColor("#c9d6e3")

BODY_F, BOLD_F, ITAL_F, BI_F = "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
SANS, SANSB = "Helvetica", "Helvetica-Bold"

S = {}
S['body'] = ParagraphStyle('body', fontName=BODY_F, fontSize=10.3, leading=14.4,
                           alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.HexColor("#111111"))
S['h1'] = ParagraphStyle('h1', fontName=SANSB, fontSize=23, leading=27, textColor=NAVY,
                         spaceBefore=0, spaceAfter=4)
S['h1sub'] = ParagraphStyle('h1sub', fontName=SANS, fontSize=10.5, leading=14,
                            textColor=ACCENT, spaceAfter=14)
S['h2'] = ParagraphStyle('h2', fontName=SANSB, fontSize=13.6, leading=17, textColor=NAVY,
                         spaceBefore=15, spaceAfter=5)
S['h3'] = ParagraphStyle('h3', fontName=SANSB, fontSize=11.1, leading=14, textColor=ACCENT,
                         spaceBefore=10, spaceAfter=3)
S['h4'] = ParagraphStyle('h4', fontName=BI_F, fontSize=10.5, leading=13.5,
                         textColor=colors.HexColor("#333333"), spaceBefore=8, spaceAfter=2)
S['bullet'] = ParagraphStyle('bullet', parent=S['body'], spaceAfter=3, leading=13.8)
S['quote'] = ParagraphStyle('quote', fontName=ITAL_F, fontSize=9.8, leading=13.4,
                            leftIndent=10*mm, rightIndent=6*mm, textColor=colors.HexColor("#44545f"),
                            spaceBefore=4, spaceAfter=7, borderPadding=0)
S['box'] = ParagraphStyle('box', parent=S['body'], fontSize=9.8, leading=13.2, spaceAfter=3)
S['boxq'] = ParagraphStyle('boxq', fontName=ITAL_F, fontSize=9.6, leading=12.8,
                           leftIndent=7*mm, textColor=colors.HexColor("#44545f"), spaceAfter=2)
S['boxh'] = ParagraphStyle('boxh', fontName=SANSB, fontSize=9.6, leading=12.6,
                           textColor=NAVY, spaceAfter=3)
S['cell'] = ParagraphStyle('cell', fontName=BODY_F, fontSize=8.8, leading=11.4)
S['cellb'] = ParagraphStyle('cellb', fontName=SANSB, fontSize=8.6, leading=11.2,
                            textColor=colors.white)
S['toc1'] = ParagraphStyle('toc1', fontName=SANSB, fontSize=10.4, leading=16, textColor=NAVY,
                           spaceBefore=6)
S['toc2'] = ParagraphStyle('toc2', fontName=BODY_F, fontSize=9.7, leading=13.4, leftIndent=8*mm)
S['title'] = ParagraphStyle('title', fontName=SANSB, fontSize=33, leading=38,
                            alignment=TA_CENTER, textColor=NAVY)
S['subtitle'] = ParagraphStyle('subtitle', fontName=SANS, fontSize=13.5, leading=19,
                               alignment=TA_CENTER, textColor=ACCENT)
S['tp'] = ParagraphStyle('tp', fontName=BODY_F, fontSize=11, leading=16,
                         alignment=TA_CENTER, textColor=colors.HexColor("#333333"))

# ---------------------------------------------------------------- inline markup
ENT = re.compile(r"&(amp|lt|gt|nbsp|mdash|ndash|bull|rarr|larr|hellip|deg|times|divide|pound|euro|ldquo|rdquo|lsquo|rsquo|#\d+);")
ENTMAP = {"amp":"&","lt":"<","gt":">","nbsp":"\u00a0","mdash":"\u2014","ndash":"\u2013",
          "bull":"\u2022","rarr":"\u2192","larr":"\u2190","hellip":"\u2026","deg":"\u00b0",
          "times":"\u00d7","divide":"\u00f7","pound":"\u00a3","euro":"\u20ac",
          "ldquo":"\u201c","rdquo":"\u201d","lsquo":"\u2018","rsquo":"\u2019"}

def _ent(m):
    k = m.group(1)
    if k.startswith("#"):
        return chr(int(k[1:]))
    return ENTMAP.get(k, m.group(0))

def inline(t):
    t = ENT.sub(_ent, t)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier" size="9">\1</font>', t)
    t = t.replace("--", "\u2013")
    return t

class Book(BaseDocTemplate):
    def __init__(self, fn):
        BaseDocTemplate.__init__(self, fn, pagesize=A4,
                                 leftMargin=22*mm, rightMargin=20*mm,
                                 topMargin=20*mm, bottomMargin=18*mm,
                                 title="The Complete IELTS Masterclass",
                                 author="Compiled from the 12-Hour IELTS Master-Course")
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id='n')
        self.addPageTemplates([
            PageTemplate(id='plain', frames=[frame]),
            PageTemplate(id='main', frames=[frame], onPage=self.decorate)])
        self.chapter = ""

    def decorate(self, canv, doc):
        canv.saveState()
        y = A4[1] - 14*mm
        canv.setStrokeColor(RULE); canv.setLineWidth(0.6)
        canv.line(22*mm, y, A4[0]-20*mm, y)
        canv.setFont(SANS, 7.6); canv.setFillColor(colors.HexColor("#7b8996"))
        canv.drawString(22*mm, y+2.4*mm, "THE COMPLETE IELTS MASTERCLASS")
        canv.drawRightString(A4[0]-20*mm, y+2.4*mm, self.chapter.upper()[:62])
        canv.setFont(SANS, 8.4); canv.setFillColor(NAVY)
        canv.drawCentredString(A4[0]/2, 11*mm, str(canv.getPageNumber()))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, '_chapter'):
            self.chapter = flowable._chapter

def callout(title, lines, bg=LIGHT, bar=ACCENT):
    inner = []
    if title:
        inner.append(Paragraph(inline(title), S['boxh']))
    for l in lines:
        if l.startswith("> "):
            inner.append(Paragraph(inline(l[2:]), S['boxq']))
        else:
            inner.append(Paragraph(inline(l), S['box']))
    t = Table([[inner]], colWidths=[166*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('LINEBEFORE', (0,0), (0,-1), 2.4, bar),
        ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    return t

def make_table(rows):
    header, body = rows[0], rows[1:]
    ncol = len(header)
    data = [[Paragraph(inline(c), S['cellb']) for c in header]]
    for r in body:
        data.append([Paragraph(inline(c), S['cell']) for c in r])
    avail = 166*mm
    if ncol == 2:   w = [avail*0.32, avail*0.68]
    elif ncol == 3: w = [avail*0.22, avail*0.39, avail*0.39]
    elif ncol == 4: w = [avail*0.16, avail*0.28, avail*0.28, avail*0.28]
    else:           w = [avail/ncol]*ncol
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f7fa")]),
        ('GRID', (0,0), (-1,-1), 0.4, RULE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    return t

# ---------------------------------------------------------------- parser
def parse(md, story, toc):
    lines = md.split("\n")
    i = 0
    bullets = []
    numbers = []
    def flush():
        nonlocal bullets, numbers
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(b), S['bullet']), leftIndent=14)
                 for b in bullets],
                bulletType='bullet', bulletFontName='Helvetica',
                bulletFontSize=7, bulletOffsetY=-1,
                start='\u25aa', leftIndent=15, bulletColor=ACCENT))
            story.append(Spacer(1, 4)); bullets = []
        if numbers:
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(b), S['bullet']), leftIndent=14) for b in numbers],
                bulletType='1', bulletFontName=SANSB, bulletFontSize=9,
                leftIndent=15, bulletColor=NAVY))
            story.append(Spacer(1, 4)); numbers = []

    while i < len(lines):
        ln = lines[i].rstrip()
        st = ln.strip()
        if st == "":
            flush(); i += 1; continue
        if st == "\\pagebreak":
            flush(); story.append(PageBreak()); i += 1; continue
        if st.startswith("|"):                       # table
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                r = lines[i].strip().strip("|")
                cells = [c.strip() for c in r.split("|")]
                if not all(set(c) <= set("-: ") and c for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                story.append(Spacer(1, 3)); story.append(make_table(rows)); story.append(Spacer(1, 8))
            continue
        if st.startswith(":::"):                     # callout
            flush()
            kind = st[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and lines[i].strip() != ":::":
                buf.append(lines[i].strip()); i += 1
            i += 1
            title = buf[0] if buf and buf[0].startswith("**") else None
            body = [b for b in buf[1:] if b] if title else [b for b in buf if b]
            bg, bar = LIGHT, ACCENT
            if kind == "warn": bg, bar = colors.HexColor("#fdf1e7"), colors.HexColor("#c0492b")
            if kind == "key":  bg, bar = colors.HexColor("#eaf3ec"), colors.HexColor("#2e7d4f")
            story.append(Spacer(1, 2))
            story.append(callout(title.strip("*") if title else None, body, bg, bar))
            story.append(Spacer(1, 8))
            continue
        if st.startswith("> "):
            flush()
            q = [st[2:]]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("> "):
                q.append(lines[i].strip()[2:]); i += 1
            qt = " ".join(q).strip()
            if qt.startswith('"') and qt.endswith('"'):
                qt = qt[1:-1]
            story.append(Paragraph("\u201c" + inline(qt) + "\u201d", S['quote']))
            continue
        if st == "---":
            flush()
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.6, color=RULE))
            story.append(Spacer(1, 6)); i += 1; continue
        if st.startswith("# "):
            flush()
            title = st[2:].strip()
            story.append(PageBreak())
            sub = ""
            if i+1 < len(lines) and lines[i+1].strip().startswith("^"):
                sub = lines[i+1].strip()[1:].strip(); i += 1
            bar = Table([[""]], colWidths=[166*mm], rowHeights=[2.6])
            bar.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),ACCENT)]))
            story.append(bar); story.append(Spacer(1, 7))
            p = Paragraph(inline(title), S['h1']); p._chapter = title
            story.append(p)
            if sub: story.append(Paragraph(inline(sub), S['h1sub']))
            else:   story.append(Spacer(1, 8))
            toc.append((1, title))
            i += 1; continue
        if st.startswith("## "):
            flush(); t = st[3:].strip()
            story.append(Paragraph(inline(t), S['h2']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE,
                                    spaceBefore=1, spaceAfter=5))
            toc.append((2, t)); i += 1; continue
        if st.startswith("### "):
            flush(); story.append(Paragraph(inline(st[4:].strip()), S['h3'])); i += 1; continue
        if st.startswith("#### "):
            flush(); story.append(Paragraph(inline(st[5:].strip()), S['h4'])); i += 1; continue
        if st.startswith("- "):
            if numbers: flush()
            bullets.append(st[2:]); i += 1; continue
        m = re.match(r"^\d+[.)]\s+(.*)", st)
        if m:
            if bullets: flush()
            numbers.append(m.group(1)); i += 1; continue
        flush()
        para = [st]; i += 1
        while i < len(lines):
            nx = lines[i].strip()
            if nx == "" or nx.startswith(("#", "-", "|", ">", ":::", "\\")) or re.match(r"^\d+[.)]\s", nx):
                break
            para.append(nx); i += 1
        story.append(Paragraph(inline(" ".join(para)), S['body']))
    flush()

# ---------------------------------------------------------------- front matter
def front_matter(story):
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph("THE COMPLETE", S['subtitle']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("IELTS<br/>MASTERCLASS", S['title']))
    story.append(Spacer(1, 6*mm))
    bar = Table([[""]], colWidths=[70*mm], rowHeights=[3])
    bar.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),ACCENT)]))
    story.append(bar)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("A Complete Preparation Course in Listening, Reading,<br/>"
                           "Writing and Speaking &mdash; Academic and General Training",
                           S['subtitle']))
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("Compiled, expanded and systematised from the complete<br/>"
                           "<b>12-Hour IELTS Master-Course of the Four Components</b><br/>"
                           "(twelve recorded live sessions, transcribed in full)", S['tp']))
    story.append(Spacer(1, 14*mm))
    story.append(Paragraph("Band 5 &rarr; Band 8+ &nbsp;&bull;&nbsp; Strategy, Language, Practice, Answer Keys",
                           S['tp']))
    story.append(PageBreak())

def toc_pages(story, toc):
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Contents", S['h1']))
    story.append(HRFlowable(width="100%", thickness=1.4, color=ACCENT, spaceAfter=8))
    for lvl, t in toc:
        story.append(Paragraph(inline(t), S['toc1'] if lvl == 1 else S['toc2']))
    story.append(PageBreak())

def main():
    files = sorted(glob.glob("book/*.md"))
    md = "\n\n".join(open(f).read() for f in files)
    # pass 1: collect TOC
    toc = []
    parse(md, [], toc)
    doc = Book("The-Complete-IELTS-Masterclass.pdf")
    story = []
    front_matter(story)
    toc_pages(story, toc)
    story.append(Paragraph("", ParagraphStyle('x')))
    body = []
    parse(md, body, [])
    story += body
    # switch template after front matter
    from reportlab.platypus import NextPageTemplate
    final = story[:]
    # insert NextPageTemplate before body
    idx = len(story) - len(body)
    final = story[:idx] + [__import__('reportlab.platypus', fromlist=['NextPageTemplate']).NextPageTemplate('main')] + body
    doc.build(final)
    print("built", os.path.getsize("The-Complete-IELTS-Masterclass.pdf"))

if __name__ == "__main__":
    main()
