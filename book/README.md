# The Complete IELTS Master Book

**📕 The book: [`The Complete IELTS Master Book.pdf`](The%20Complete%20IELTS%20Master%20Book.pdf)** — 209 pages,
about 81,000 words.

A single-volume, self-contained IELTS preparation course covering all four components — Listening, Reading,
Writing and Speaking. Compiled by studying every one of the twelve lessons in the
*IELTS 12 Hours Full Course for Beginners 2023 — Master-Course of 4 Components* video series that sits in
the root of this repository, then reorganised and expanded into reference and practice form.

---

## What is in the book

| Part | Contents |
|---|---|
| **Foundations (Ch. 1–5)** | Full test format, scoring and band conversion; band descriptors decoded criterion by criterion; 8-week and 21-day study plans; core grammar for Band 7+; the Academic Word List and a paraphrase system |
| **Listening (Ch. 6–8)** | Every question type with procedure and traps; nine micro-skills (numbers, spelling, distractors, signposts, accents, note-taking); **complete practice test with recording script, answer key and trap-by-trap explanations** |
| **Reading (Ch. 9–12)** | All ten question types; skimming, scanning and the NOT GIVEN logic; timing discipline; **complete practice test with three original passages and full explanations** |
| **Writing (Ch. 13–17)** | Task 1 for all seven visual types with four Band 9 models; Task 2 structures for all five essay types; a Band 6 vs 7 vs 8 comparison of the same question; a 40-item error repair manual; General Training letters |
| **Speaking (Ch. 18–21)** | The AREA method, 30 model Part 1 answers, 15 cue cards, Part 3 discussion technique, and a pronunciation programme with stress and intonation drills |
| **Practice and rehearsal (Ch. 22–27)** | **A second listening test** (scripts + key), **two further complete Reading tests with keys**, a full mock Writing and Speaking paper with Band 8–9 model answers, **ten model Task 2 essays** across the most common topics, and the exam-day playbook |
| **Appendices (A–D)** | Language reference (AWL, linking words, irregular verbs, spelling rules); topic vocabulary bank for 15 themes; **a lesson-by-lesson companion to the video course**; 50 practice prompts and drills with a seven-week rotation |

Everything is original except where it explicitly quotes the format of the exam. The video course taught the
techniques; every practice question, model answer, explanation, grammar reference and study plan here was
written for this edition.

## How it was made

1. **Every lesson was studied in full.** The twelve video parts (~11.5 hours, 57 minutes each) were
   extracted to audio and transcribed end to end — **5,654 segments, about 79,000 words of spoken
   teaching**. The verbatim transcripts are in [`transcripts/`](transcripts/) as the working record.
2. **On-screen material was captured and read.** Frames were sampled at 2-second intervals and the
   whiteboard and past-paper content was extracted with OCR to confirm the question types, answer keys and
   worked examples the instructor referred to.
3. **The teaching was mapped.** A coverage matrix was built across all twelve lessons to identify which
   component and which question type each lesson addressed, and how much time it received — that mapping
   produced the lesson-by-lesson companion in Appendix C and the chapter structure of the book.
4. **The book was written** as structured Markdown and typeset to PDF.

## Repository layout

```
book/
├── The Complete IELTS Master Book.pdf   ← the deliverable
├── README.md                            ← this file
├── book.json                            ← chapter manifest (order + titles)
├── build_book.py                        ← Markdown → PDF renderer (ReportLab)
├── src/                                 ← 31 Markdown chapter sources
└── transcripts/                         ← verbatim text of all 12 lessons, with timestamps
```

## Rebuilding the PDF

Requires Python 3 with `reportlab` and `pillow`.

```bash
cd book
pip install reportlab pillow
python3 build_book.py "The Complete IELTS Master Book.pdf"
```

The renderer supports a small Markdown dialect: `#`–`####` headings, tables, bulleted and numbered lists,
code blocks, horizontal rules, `<!-- pagebreak -->` for page breaks, and callout boxes written as
`[tip] …`, `[warn] …`, `[note] …` or `[exam] …`. It produces a cover, an automatically generated table of
contents with page numbers, PDF bookmarks and running headers.

## Verification

- **Pages:** 209 · **Words in rendered PDF:** ~81,000 · **File size:** ~0.9 MB
- **Practice material:** 3 complete Reading tests (120 questions), 2 complete Listening tests (80 questions
  in exam format, each with a recording script), 1 complete Writing and Speaking mock, and 4 full Task 1
  model answers at Band 9 plus 10 model essays and 4 further model essays inside the comparison chapter.
- **Answer keys:** every test includes a key with explanations that identify the specific trap used in each
  question, plus diagnostic tables for converting raw scores to bands.

## Note on the source material

The video lessons work through extracts from published practice papers. The book deliberately does **not**
reproduce those extracts; it substitutes original questions written in identical formats so that every task
here can be attempted, marked and repeated freely. The transcripts in `transcripts/` are machine-generated
records of the spoken teaching, included as evidence of the study process and to allow the reader to verify
where each technique in the book came from.
