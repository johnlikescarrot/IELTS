# IELTS

Source recordings of the **12 Hours Full Course for Beginners — Master-Course of the 4 Components**, plus a complete preparation book compiled from them.

## The book

**[The-Complete-IELTS-Masterclass.pdf](The-Complete-IELTS-Masterclass.pdf)** — 98 pages, ~35,500 words.

A full IELTS preparation course in Listening, Reading, Writing (Academic and General Training) and Speaking, built entirely from a study of the twelve video parts in this repository. Every rule the teacher states, every correction he makes to a student's live answer, and every exercise he sets has been gathered, made explicit and expanded into reference form, with band descriptor tables, language banks, worked model answers, practice sets and answer keys added.

### Contents

| Chapter | Subject |
| --- | --- |
| — | How this book was made — provenance and method |
| 1 | The test, the scoring, and the strategy behind both |
| 2 | Listening — all ten question types, prediction, distractors, maps, numbers |
| 3 | Reading — skimming/scanning, paraphrase, T/F/NG, headings, GT specifics |
| 4 | Academic Writing Task 1 — graphs, charts, tables, processes, maps |
| 5 | General Training Writing Task 1 — the letter, three registers |
| 6 | Writing Task 2 — five question types, PEEL, cohesion, model essays |
| 7 | Speaking — three parts, four criteria, cue cards, Part 3 discussion |
| 8 | Reading the band descriptors like an examiner |
| 9 | Grammar for range and accuracy |
| 10 | Vocabulary, collocation and paraphrase |
| 11 | Pronunciation |
| 12 | Study plans and exam-day management |
| 13 | Appendices — every list gathered for final-week revision |

## Repository layout

```
The-Complete-IELTS-Masterclass.pdf   the book
book/                                 markdown sources, one file per chapter
transcripts/                          full transcripts of all 12 video parts
tools/transcribe.py                   audio extraction + ASR pipeline
tools/build_pdf.py                    markdown -> typeset PDF
*.mp4                                 the original twelve course recordings
```

## Rebuilding the PDF

```bash
pip install reportlab
cd tools && python build_pdf.py     # reads ../book/*.md
```

## How the videos were studied

Audio was extracted from all twelve `.mp4` parts at 16 kHz mono, segmented at low-energy points into chunks of up to twenty seconds, and transcribed with an on-device ASR model. The resulting timestamped transcripts (in `transcripts/`) total roughly 420 KB and cover the full twelve hours. They were then read in full, and the book was written from them.

The transcripts are machine-generated and contain recognition errors, particularly around proper nouns and non-English speech; they are included for traceability rather than as a polished artefact. The book itself is written prose.
