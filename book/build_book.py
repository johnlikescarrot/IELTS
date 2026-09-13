#!/usr/bin/env python3
"""
IELTS Master Book — Markdown -> PDF renderer (ReportLab).

Reads a manifest (book.json) listing chapter markdown files, renders a
professionally typeset PDF with cover, TOC with page numbers, running
headers/footers, tables, callout boxes, code blocks and inline images.

Usage:  python3 build_book.py [output.pdf]
"""
import json
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image,
                                KeepTogether, ListFlowable, ListItem, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, 'content')

# ---------------------------------------------------------------- palette ----
NAVY = colors.HexColor('#0f2d52')
BLUE = colors.HexColor('#1c5d99')
ACCENT = colors.HexColor('#c0392b')
LIGHT = colors.HexColor('#eef3f9')
MID = colors.HexColor('#d6e2f0')
GREY = colors.HexColor('#555555')
GREEN = colors.HexColor('#1e7a4f')

def _register_fonts():
    """Try DejaVu (better glyph coverage); fall back to built-ins."""
    candidates = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 'BodySerif'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'BodySans'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'BodySans-Bold'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf', 'BodySans-Italic'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 'BodyMono'),
    ]
    ok = {}
    for path, name in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                ok[name] = name
            except Exception:
                pass
    return ok

FONTS = _register_fonts()
BASE = 'BodySerif' if 'BodySerif' in FONTS else 'Times-Roman'
BASE_B = 'BodySans-Bold' if 'BodySans-Bold' in FONTS else 'Helvetica-Bold'
BASE_R = 'BodySans' if 'BodySans' in FONTS else 'Helvetica'
BASE_I = 'BodySans-Italic' if 'BodySans-Italic' in FONTS else 'Helvetica-Oblique'
MONO = 'BodyMono' if 'BodyMono' in FONTS else 'Courier'

# ------------------------------------------------------------------ styles ---
ss = getSampleStyleSheet()
S = {}
S['body'] = ParagraphStyle('body', fontName=BASE, fontSize=10.2, leading=14.6,
                           alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.HexColor('#1a1a1a'))
S['body_first'] = ParagraphStyle('body_first', parent=S['body'], spaceBefore=2)
S['h1'] = ParagraphStyle('h1', fontName=BASE_B, fontSize=21, leading=25, textColor=NAVY,
                         spaceBefore=10, spaceAfter=4)
S['h2'] = ParagraphStyle('h2', fontName=BASE_B, fontSize=14.5, leading=18, textColor=BLUE,
                         spaceBefore=13, spaceAfter=5)
S['h3'] = ParagraphStyle('h3', fontName=BASE_B, fontSize=11.8, leading=15, textColor=colors.HexColor('#25405e'),
                         spaceBefore=10, spaceAfter=4)
S['h4'] = ParagraphStyle('h4', fontName=BASE_B, fontSize=10.4, leading=13.6, textColor=colors.HexColor('#333333'),
                         spaceBefore=8, spaceAfter=3)
S['bullet'] = ParagraphStyle('bullet', parent=S['body'], fontSize=10.1, leading=14.0, spaceAfter=2.5,
                             alignment=TA_LEFT)
S['quote'] = ParagraphStyle('quote', parent=S['body'], fontName=BASE_I, fontSize=9.9, leading=14,
                            textColor=colors.HexColor('#2c3e50'), alignment=TA_LEFT)
S['code'] = ParagraphStyle('code', fontName=MONO, fontSize=8.2, leading=11.4,
                           textColor=colors.HexColor('#12303f'))
S['caption'] = ParagraphStyle('caption', fontName=BASE_I, fontSize=8.4, leading=11, alignment=TA_CENTER,
                              textColor=GREY, spaceBefore=2, spaceAfter=8)
S['toc1'] = ParagraphStyle('toc1', fontName=BASE_B, fontSize=10.6, leading=18, textColor=NAVY)
S['toc2'] = ParagraphStyle('toc2', fontName=BASE_R, fontSize=9.4, leading=14, leftIndent=12)
S['toc3'] = ParagraphStyle('toc3', fontName=BASE_R, fontSize=8.6, leading=12.5, leftIndent=24,
                           textColor=GREY)
S['cover_title'] = ParagraphStyle('cover_title', fontName=BASE_B, fontSize=34, leading=40,
                                  alignment=TA_CENTER, textColor=colors.white)
S['cover_sub'] = ParagraphStyle('cover_sub', fontName=BASE_R, fontSize=14.5, leading=20,
                                alignment=TA_CENTER, textColor=colors.HexColor('#cfe0f5'))
S['cover_meta'] = ParagraphStyle('cover_meta', fontName=BASE_R, fontSize=10.5, leading=15,
                                 alignment=TA_CENTER, textColor=colors.HexColor('#e8eef7'))
S['table_cell'] = ParagraphStyle('table_cell', fontName=BASE, fontSize=8.9, leading=12)
S['table_head'] = ParagraphStyle('table_head', fontName=BASE_B, fontSize=9.1, leading=12.2,
                                 textColor=colors.white)

# ------------------------------------------------------------- md parsing ----
INLINE_RE = [
    (re.compile(r'\*\*\*(.+?)\*\*\*'), r'<b><i>\1</i></b>'),
    (re.compile(r'\*\*(.+?)\*\*'), r'<b>\1</b>'),
    (re.compile(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])'), r'<i>\1</i>'),
    (re.compile(r'`([^`]+?)`'), r'<font face="%s" size="9">\1</font>' % MONO),
]

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

TAG_RE = re.compile(r'<(/?)(b|i|font)[^>]*>')

def _balanced(t):
    stack = []
    for m in TAG_RE.finditer(t):
        closing, tag = m.group(1), m.group(2)
        if closing:
            if not stack or stack[-1] != tag:
                return False
            stack.pop()
        else:
            stack.append(tag)
    return not stack

def inline(t):
    t = esc(t)
    out = t
    for rx, rep in INLINE_RE:
        out = rx.sub(rep, out)
    if _balanced(out):
        return out
    # fallback: drop all emphasis markers, keeping text intact and balanced
    plain = t.replace('*', '')
    return plain

def parse_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        rows.append(cells)
    if len(rows) >= 2 and re.match(r'^[\s:\-|]+$', lines[1].strip()):
        rows.pop(1)
    return rows

def table_flowable(rows, col_widths=None):
    if not rows:
        return Spacer(1, 0)
    ncol = max(len(r) for r in rows)
    data = []
    for i, r in enumerate(rows):
        r = r + [''] * (ncol - len(r))
        st = S['table_head'] if i == 0 else S['table_cell']
        data.append([Paragraph(inline(c), st) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, MID),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    t.setStyle(TableStyle(style))
    return t

def callout(text, kind='tip'):
    colours = {'tip': (colors.HexColor('#f2f8f3'), GREEN, colors.HexColor('#d5ead9')),
               'warn': (colors.HexColor('#fdf3f2'), ACCENT, colors.HexColor('#f3d3cf')),
               'note': (colors.HexColor('#f1f6fc'), BLUE, colors.HexColor('#cfe0f0')),
               'exam': (colors.HexColor('#fdf8ec'), colors.HexColor('#8a6d1f'), colors.HexColor('#f0e2bd'))}
    bg, bar, border = colours.get(kind, colours['note'])
    st = ParagraphStyle('co', parent=S['quote'], fontName=BASE, textColor=colors.HexColor('#1f2d3d'))
    p = Paragraph(inline(text), st)
    t = Table([[p]], colWidths=[16.4 * cm], hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg),
                           ('LINEBEFORE', (0, 0), (0, 0), 2.6, bar),
                           ('BOX', (0, 0), (-1, -1), 0.4, border),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                           ('TOPPADDING', (0, 0), (-1, -1), 6),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    return t

def md_to_flowables(text, book):
    """Convert markdown text into a list of flowables."""
    out = []
    lines = text.split('\n')
    i = 0
    para = []
    def flush():
        nonlocal para
        if para:
            out.append(Paragraph(inline(' '.join(para).strip()), S['body']))
            para = []
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith('<!--') and s.endswith('-->'):
            cmd = s.strip('<!-> ').strip().lower()
            flush()
            if cmd == 'pagebreak':
                out.append(PageBreak())
            elif cmd.startswith('image'):
                m = re.match(r'image\s+(\S+)\s*(.*)', cmd)
                if m:
                    out.extend(image_flowables(m.group(1), m.group(2)))
            i += 1
            continue
        if not s:
            flush(); i += 1; continue
        if s.startswith('```'):
            flush()
            lang = s[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            body = '<br/>'.join(esc(b).replace(' ', '&nbsp;') for b in buf)
            t = Table([[Paragraph(body, S['code'])]], colWidths=[16.4 * cm], hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f6f8')),
                                   ('BOX', (0, 0), (-1, -1), 0.4, MID),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 7),
                                   ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                                   ('TOPPADDING', (0, 0), (-1, -1), 5),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
            out.append(t); out.append(Spacer(1, 6))
            continue
        if s.startswith('!['):   # markdown image
            m = re.match(r'!\[(.*?)\]\((\S+?)\)', s)
            if m:
                flush(); out.extend(image_flowables(m.group(2), m.group(1)))
            i += 1; continue
        if s.startswith('|') and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set('|:- '):
            flush()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl.append(lines[i]); i += 1
            out.append(table_flowable(parse_table(tbl)))
            out.append(Spacer(1, 8))
            continue
        if s == '---':
            flush(); out.append(HRFlowable(width='100%', thickness=0.7, color=MID,
                                           spaceBefore=6, spaceAfter=8))
            i += 1; continue
        m = re.match(r'^(#{1,5})\s+(.*)$', s)
        if m:
            flush()
            lvl = len(m.group(1)); title = m.group(2).strip()
            if lvl == 1:
                book_chapter(out, title, book)
            else:
                st = S['h2'] if lvl == 2 else (S['h3'] if lvl == 3 else S['h4'])
                pl = re.sub(r'[*`]', '', title)
                p = Paragraph(inline(title), st)
                p._toc_level = lvl - 1
                p._toc_text = pl
                out.append(p)
            i += 1; continue
        m_co = re.match(r'^\[(tip|warn|note|exam)\]\s*(.*)$', s, re.I)
        if m_co and not para:
            flush()
            kind = m_co.group(1).lower()
            buf = [m_co.group(2)]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,5}\s|[-*+]\s|\d+[.)]\s|\||>|```)', lines[i].strip()):
                buf.append(lines[i].strip())
                i += 1
            out.append(callout(' '.join(buf).strip(), kind))
            out.append(Spacer(1, 7))
            continue
        if s.startswith('> '):
            flush()
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            kind = 'note'
            raw = ' '.join(buf)
            m = re.match(r'^\[(tip|warn|note|exam)\]\s*(.*)$', raw, re.I)
            if m:
                kind = m.group(1).lower(); raw = m.group(2)
            out.append(callout(raw, kind)); out.append(Spacer(1, 7))
            continue
        if re.match(r'^[-*+]\s+', s):
            flush()
            items = []
            while i < len(lines) and re.match(r'^\s*[-*+]\s+', lines[i]):
                sub = re.sub(r'^\s*[-*+]\s+', '', lines[i])
                items.append(ListItem(Paragraph(inline(sub), S['bullet']), leftIndent=16))
                i += 1
            out.append(ListFlowable(items, bulletType='bullet', start='•', bulletFontSize=8,
                                    leftIndent=12, bulletOffsetY=1))
            out.append(Spacer(1, 5))
            continue
        if re.match(r'^\d+[.)]\s+', s):
            flush()
            items = []
            while i < len(lines) and re.match(r'^\s*\d+[.)]\s+', lines[i]):
                sub = re.sub(r'^\s*\d+[.)]\s+', '', lines[i])
                items.append(ListItem(Paragraph(inline(sub), S['bullet']), leftIndent=18))
                i += 1
            out.append(ListFlowable(items, bulletType='1', leftIndent=14, bulletFontSize=9.6))
            out.append(Spacer(1, 5))
            continue
        if s.startswith(':::'):
            i += 1; continue
        para.append(s)
        i += 1
    flush()
    return out

def image_flowables(path, caption=''):
    p = path if os.path.isabs(path) else os.path.join(CONTENT, path)
    if not os.path.exists(p):
        return []
    from PIL import Image as PILImage
    iw, ih = PILImage.open(p).size
    maxw = 16.0 * cm
    maxh = 19.0 * cm
    scale = min(maxw / iw, maxh / ih, 1.0)
    img = Image(p, width=iw * scale, height=ih * scale)
    img.hAlign = 'CENTER'
    fl = [img]
    if caption:
        fl.append(Paragraph(inline(caption), S['caption']))
    return fl

def book_chapter(out, title, book):
    """Start a new chapter page with a decorative heading."""
    out.append(PageBreak())
    num = book.chapter_no + 1
    book.chapter_no = num
    book.current_chapter = title
    band = Table([[Paragraph(f'<font size="9" color="#cfe0f5">CHAPTER {num}</font>', S['h1'])]],
                 colWidths=[16.4 * cm])
    band._toc_level = 0
    band._toc_text = f'Chapter {num}: {title}'
    band.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY),
                              ('LEFTPADDING', (0, 0), (-1, -1), 10),
                              ('TOPPADDING', (0, 0), (-1, -1), 8),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    out.append(band)
    head = Paragraph(f'<font color="#ffffff">{inline(title)}</font>',
                     ParagraphStyle('ch', parent=S['h1'], fontSize=18, leading=22))
    hb = Table([[head]], colWidths=[16.4 * cm])
    hb.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 10)]))
    out.append(hb)
    out.append(Spacer(1, 12))

# ------------------------------------------------------------------- doc -----
class BookDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4,
                         leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                         topMargin=2.0 * cm, bottomMargin=1.8 * cm,
                         title='The Complete IELTS Master Book',
                         author='Compiled from the IELTS Master Course video series',
                         subject='IELTS preparation', **kw)
        self.chapter_no = 0
        self.current_chapter = 'Front Matter'
        self._toc_entries = []
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='body')
        self.addPageTemplates([
            PageTemplate(id='cover', frames=[Frame(0, 0, A4[0], A4[1], id='c')], onPage=self.cover_page),
            PageTemplate(id='plain', frames=[frame], onPage=self.plain_page),
            PageTemplate(id='body', frames=[frame], onPageEnd=self.body_page),
        ])

    def cover_page(self, canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canv.setFillColor(colors.HexColor('#1c5d99'))
        canv.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, stroke=0, fill=1)
        canv.restoreState()

    def plain_page(self, canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, 0, A4[0], 0.9 * cm, stroke=0, fill=1)
        canv.setFont(BASE_R, 8)
        canv.setFillColor(colors.white)
        canv.drawCentredString(A4[0] / 2, 0.32 * cm, 'The Complete IELTS Master Book')
        canv.restoreState()

    def body_page(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(MID)
        canv.setLineWidth(0.6)
        canv.line(doc.leftMargin, A4[1] - 1.35 * cm, A4[0] - doc.rightMargin, A4[1] - 1.35 * cm)
        canv.setFont(BASE_R, 8)
        canv.setFillColor(GREY)
        canv.drawString(doc.leftMargin, A4[1] - 1.25 * cm, 'THE COMPLETE IELTS MASTER BOOK')
        ch = (doc.current_chapter or '')[:70]
        canv.drawRightString(A4[0] - doc.rightMargin, A4[1] - 1.25 * cm, ch)
        canv.line(doc.leftMargin, 1.35 * cm, A4[0] - doc.rightMargin, 1.35 * cm)
        canv.setFont(BASE_R, 8.5)
        canv.drawCentredString(A4[0] / 2, 0.95 * cm, str(canv.getPageNumber()))
        canv.restoreState()

    def handle_documentBegin(self):
        self._toc_entries = []
        super().handle_documentBegin()

    def afterFlowable(self, flowable):
        lvl = getattr(flowable, '_toc_level', None)
        if lvl is None:
            return
        text = getattr(flowable, '_toc_text', None)
        if text is None:
            text = re.sub(r'<[^>]+>', '', flowable.getPlainText())
        # outline levels must start at 0 and never skip a level
        if not self._toc_entries:
            lvl = 0
        else:
            lvl = min(lvl, self._toc_entries[-1][0] + 1)
        if lvl == 0:
            self.current_chapter = text
        key = f'h{len(self._toc_entries)}'
        self._toc_entries.append((lvl, text))
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text[:90], key, level=min(lvl, 3), closed=(lvl == 0))
        self.notify('TOCEntry', (lvl, text, self.page, key))


class Book:
    """Holds rendering state used while the story is assembled."""
    def __init__(self, doc):
        self.doc = doc
        self.chapter_no = 0
        self.current_chapter = 'Front Matter'

# ------------------------------------------------------------------ main -----
def build(out_path):
    manifest = json.load(open(os.path.join(HERE, 'book.json')))
    doc = BookDoc(out_path)
    book = Book(doc)
    doc._book = book
    story = []

    # --- cover ---
    story.append(NextPageTemplate('cover'))
    story.append(Spacer(1, 5.2 * cm))
    story.append(Paragraph(manifest['title'], S['cover_title']))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(manifest.get('subtitle', ''), S['cover_sub']))
    story.append(Spacer(1, 6.0 * cm))
    for line in manifest.get('cover_lines', []):
        story.append(Paragraph(line, S['cover_meta']))
    story.append(NextPageTemplate('plain'))
    story.append(PageBreak())

    # --- front matter (copyright / how to use) ---
    fm = os.path.join(CONTENT, 'front_matter.md')
    if os.path.exists(fm):
        txt = open(fm).read()
        # split: first part before TOC marker goes here, rest after TOC
        if '<!-- TOC -->' in txt:
            before, after = txt.split('<!-- TOC -->', 1)
        else:
            before, after = txt, ''
        story.extend(md_to_flowables(before, book))

    # --- table of contents ---
    story.append(PageBreak())
    story.append(Paragraph('Table of Contents', S['h1']))
    story.append(Spacer(1, 6))
    toc = TableOfContents()
    toc.levelStyles = [S['toc1'], S['toc2'], S['toc3']]
    toc.dotsMinLevel = 0
    story.append(toc)

    if os.path.exists(fm):
        txt = open(fm).read()
        if '<!-- TOC -->' in txt:
            after = txt.split('<!-- TOC -->', 1)[1]
            story.append(PageBreak())
            story.extend(md_to_flowables(after, book))

    story.append(NextPageTemplate('body'))

    # --- chapters ---
    for ch in manifest['chapters']:
        path = os.path.join(CONTENT, ch['file'])
        if not os.path.exists(path):
            print('  ! missing chapter', ch['file'])
            continue
        text = open(path).read()
        story.extend(md_to_flowables(text, book))
        print(f"  + {ch['file']}")

    # multi-build for TOC
    doc.multiBuild(story)
    return out_path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'IELTS_Master_Book.pdf')
    p = build(out)
    print('wrote', p, os.path.getsize(p) / 1e6, 'MB')
