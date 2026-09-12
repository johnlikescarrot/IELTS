# IELTS

Twelve-part video course: *IELTS 12 Hours Full Course for Beginners 2023 — Master-Course of 4 Components*
(part 1 … part 12, roughly 11.5 hours of teaching in total).

## 📕 The Complete IELTS Master Book

A 209-page, ~81,000-word preparation book covering **Listening, Reading, Writing and Speaking**, compiled by
studying all twelve lessons in full.

**→ [`book/The Complete IELTS Master Book.pdf`](book/The%20Complete%20IELTS%20Master%20Book.pdf)**

### What is inside

- **Foundations** — test format and scoring, band descriptors decoded criterion by criterion, 8-week and
  21-day study plans, core grammar for Band 7+, the Academic Word List and a paraphrase system
- **Listening** — every question type with procedures and traps, nine micro-skills, and **two complete
  practice tests** with recording scripts, answer keys and trap-by-trap explanations
- **Reading** — all ten question types, skimming/scanning/NOT GIVEN logic, timing discipline, and **three
  complete practice tests** (120 questions) with three original passages each and full explanations
- **Writing** — Task 1 for all seven visual types with four Band 9 models, Task 2 structures for all five
  essay types, a Band 6 vs 7 vs 8 comparison of the same question, a 40-item error repair manual, **ten
  model essays**, and General Training letters
- **Speaking** — the AREA method, 30 model Part 1 answers, 15 cue cards, Part 3 discussion technique, and a
  pronunciation programme with stress and intonation drills
- **Rehearsal** — a full mock Writing and Speaking paper with model answers, and the exam-day playbook
- **Appendices** — language reference, topic vocabulary for 15 themes, a lesson-by-lesson companion to this
  video course, and 50 practice prompts with a seven-week rotation

### How it was built

All twelve lessons were transcribed end to end (**5,654 segments, ~79,000 words of spoken teaching**), the
on-screen material was captured and read by OCR, and the teaching was mapped lesson by lesson before the
book was written and typeset. The working materials are included:

| Path | Contents |
|---|---|
| [`book/The Complete IELTS Master Book.pdf`](book/The%20Complete%20IELTS%20Master%20Book.pdf) | The book |
| [`book/src/`](book/src) | 31 Markdown chapter sources |
| [`book/transcripts/`](book/transcripts) | Verbatim timestamped transcripts of all 12 lessons |
| [`book/build_book.py`](book/build_book.py) | Markdown → PDF renderer used to typeset the book |
| [`book/README.md`](book/README.md) | Full description, contents table and rebuild instructions |

```bash
cd book && pip install reportlab pillow && python3 build_book.py "The Complete IELTS Master Book.pdf"
```

## The videos

The twelve `part*.mp4` files in this repository are the source course material. Each part is roughly
57 minutes and covers one lesson of the course; Appendix C of the book maps each lesson to the chapter of
the book that develops it.
