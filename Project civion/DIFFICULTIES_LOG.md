# Civion – Difficulties Log

Running list of problems found while building Civion, for the final report.

**For any human or LLM working on this repo:** if you hit a problem, add it here under the right section (or a new one). One bullet per issue: bold title, what happened, and a tag: **(verified)** = checked against the PDF/code, **(estimate)** = not checked. Don't delete old entries. If one gets fixed, add "→ Fixed: how, date". This file is a findings log only; it doesn't authorise code changes.

## 1. Current extraction (parser.py)
- **12,000-character truncation (verified).** parser.py sends only `clean_text[:12000]` to the LLM. On the BLR spec (51 pages, ~127,000 chars) the cut ends on page 7, inside the reference list and LEED text. None of the in-scope clauses reach the LLM; the first one (2.3 Grades of Concrete) starts at about char 38,850.
- **Single call, not several prompts (verified).** It had been described as several sequential prompts, but the code makes one Groq call. It was merged from three calls because the Groq free tier (~8,000 tokens/min) caused rate-limit retries of 5–45 s each.
- **Token limit (estimate).** The whole BLR document is ~32,000 tokens (4 chars per token), so it can't go to Groq in one call on the free tier.
- **Model decommissioned silently (from project notes).** The previous Groq model was retired, and every extraction returned nothing until someone noticed.

## 2. Document structure
- **Relevant content is larger and more scattered than expected (verified).** In-scope sections are ~38% of BLR (~48,000 chars), not 5–7 pages.
- **Small relevant clauses sit inside out-of-scope sections (verified).** Nominal cover is under Reinforcement (3.5 F). The sampling table appears before the Field Quality Control heading (3.9).
- **No table of contents, and layout differs between authors.** A numbering regex like "2.6" was rejected because other documents number their clauses differently.

## 3. PDF parsing (PyMuPDF4LLM)
- **Repeated page header/footer.** "SOM INDIA LLC" and the copyright line repeat ~54 times, sometimes mid-clause.
- **Table errors.** The Table 6 header text is split across columns. Table 6 row 2 has two values stacked in one cell. In Table 7, the chlorides and suspended-matter rows are merged into one row.
- **Unneeded OCR.** RapidOCR ran on pages 5, 25, 27, 33 and 50 although the PDF is digital; those pages need checking for errors.
- **Missed headings (verified for 2.6).** 2.6 Water, 2.11 Mass Concrete and 3.6 Concrete came out as bold list items ("- **2.6 WATER**"), not "#" headings, although they look like the other headings in the PDF. For 2.6 the likely cause is that it directly follows a numbered list (items 1–6 under 2.5 C), so the parser treated it as item 7. Not yet confirmed for 2.11 and 3.6. Lesson: don't trust the parser's heading labels.
- **Sampling table garbled (verified in both pdfplumber and PyMuPDF output).** The text reads "Up to 5 cu.m. in a day 15 cu.m. to 15 cu.m. 2". This is probably "1" plus "5 cu.m. to 15 cu.m." merged together. Still to be checked visually in the PDF.


