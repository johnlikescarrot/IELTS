# IELTS Master Guide — The Complete Preparation Book

A comprehensive IELTS preparation book compiled from a complete, end-to-end study of the
**“IELTS 12 Hours Full Course for Beginners 2023 — Master-Course of 4 Components”**
video course in this repository.

**Deliverable:** [`IELTS_Master_Guide.pdf`](IELTS_Master_Guide.pdf) — 63 pages, A4.

## What is inside

The book covers the whole test for **Academic and General Training**:

- **Front matter** — About this book, how the 12 video parts map to the book, a one-page
  tour of the test, and how to use the book.
- **Chapters 1–2** — What IELTS is, Academic vs General Training, test-day logistics, and
  how the band score is calculated (raw-score → band conversion tables).
- **Chapters 3–5** — Listening: format, question types, instruction language (spelling,
  numbers, maps, ONE WORD ONLY …), then a full Section 1–4 practice set with model answers.
- **Chapters 6–9** — Reading: format and strategy (the four-step method, skimming/scanning,
  paraphrase), every question type with decision rules, then worked passages with answer keys.
- **Chapters 10–14** — Writing: overview and criteria, Task 1 Academic report (introduction +
  overview formulas, trend language), Task 1 General Training letter (tone, openings,
  closings), Task 2 essay (five types, structure, task response), and the grammar & cohesion
  toolkit (linkers, tense choice, complex sentences).
- **Chapters 15–17** — Speaking: format, the four band criteria, Part 1/2/3 technique, and
  model answers.
- **Chapters 18–20** — Vocabulary builder (synonyms, topic banks, idioms), band-score
  arithmetic and 4-week / 8-week study plans, and quick-reference checklists.
- **Appendices A–C** — Full course map, additional model answers, and a glossary of IELTS terms.

Every technique, model answer, table and rule taught in the twelve hours of the source
course has been identified, organised, expanded and rewritten into this structured reference.

## Repository layout

```
book/
├── IELTS_Master_Guide.pdf   # the published book (build output)
├── build_book.py            # ReportLab builder (pure Python)
├── content/                 # lightweight-markup manuscript, one file per chapter
│   ├── 00_front.txt … 17_appendix.txt
└── README.md
```

## Rebuilding the PDF

Requires Python 3 and the `reportlab` library:

```bash
pip install reportlab
python3 book/build_book.py
```

The builder parses the lightweight markup in `content/*.txt`:

| Markup | Meaning |
| ------ | ------- |
| `# `, `## `, `### ` | Chapter / section / subsection headings |
| `- `, `+ ` | Bullets / auto-numbered steps |
| `> TIP:` `> WARNING:` | Shaded callout boxes |
| `<<<` … `>>>` | Bordered model-answer box |
| `[[table:Caption]]` … `\| a \| b \|` | Table (closes at the first non-row line) |
| `---` | Horizontal rule |
| `[[[TOC]]]` | Table-of-contents sentinel (injected after the cover) |
| `**bold**`, `*italic*` | Inline formatting |
