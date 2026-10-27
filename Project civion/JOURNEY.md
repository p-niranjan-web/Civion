# Civion – Development Journey

This file records how Civion's document-processing pipeline evolved: what we tried, what went wrong, and what we decided at each stage. It is written as source material for the final report.

Anyone (human or AI) working on the repo should add to it when something new is tried or a problem is found. Add new stages at the end, in the same style. Mark anything not checked against the PDF or code as *(not verified)*.

---

## Stage 0 – Early attempt: RAG over IS 456

The first idea was to work directly from the IS code using retrieval (RAG):

1. Parse IS 456 with a structure-aware PDF parser (a PyPDF-style library) and split it into chunks by sub-section.
2. Store the chunks for retrieval.
3. Compare the specification with IS 456 sentence by sentence: for each sentence in the spec, retrieve the matching IS 456 clause and check it.

**Why it failed:**
- **IS 456 is not self-contained.** Many clauses send the reader elsewhere: to other IS codes (e.g. IS 383 for aggregates, IS 516 for testing) or to other clauses and tables of IS 456 itself. A retrieved chunk often lacked the actual requirement, so a sentence-level comparison had nothing concrete to compare against.
- **The PDF text was unreliable.** The IS 456 PDF looks digital but is a scanned copy with an OCR text layer. Extracted or copied text did not match what is printed: for example, clause "5.1" came out as "S.1". Clause numbers, values and units could not be trusted.

**Decision:** drop RAG over the raw code. Instead, identify the parameters that actually recur in real specifications, and hand-build the IS 456 requirements as structured data (`database.py`), checked manually. Compliance is then decided by deterministic Python (`auditor.py`), not by retrieval.

---

## Stage 1 – Starting point

Civion checks construction specification PDFs against IS 456:2000. The original pipeline:

1. `parser.py` extracts the PDF text with **pdfplumber**, keeping table rows as `cell | cell | cell`.
2. The text is truncated and sent to **one Groq LLM call** (`openai/gpt-oss-120b`), which returns ~40 parameters as JSON, each with a source quote.
3. `auditor.py` (pure Python, no LLM) compares the values with the hardcoded IS 456 tables in `database.py` and returns PASS / FAIL / MISSING.

```python
# parser.py
text_chunk = clean_text[:12000]
```

The extraction originally used three sequential LLM calls. It was merged into a single call because the Groq free tier (~8,000 tokens per minute) triggered rate-limit retries of 5–45 s per call. Earlier, the default Groq model was decommissioned and every extraction silently returned nothing until the model name was updated.

This worked on the short sample specs used during development.

---

## Stage 2 – Testing on a real, long specification

**Test document:** BLR Airport, Section 03 30 00 "Cast-in-Place Concrete" (SOM India). It is 51 pages, digitally produced, and has no table of contents.

**Problem 1: truncation removes everything relevant.**
The full text is ~127,000 characters. The 12,000-character cut ends on page 7, inside the reference list and LEED requirements. The first in-scope clause (2.3 Grades of Concrete) starts at about character 38,850, so **none of the relevant clauses reached the LLM**.

**Problem 2: the whole document is too large to send.**
~127,000 characters is roughly 32,000 tokens (estimate, ~4 characters per token). That is far above the Groq free-tier limit of ~8,000 tokens per minute, so it can't go in one call.

**Problem 3: relevant content is large and scattered.**
The in-scope sections make up about 38% of the document (~48,000 characters), not the 5–7 pages first assumed. Some needed values sit inside sections that are otherwise out of scope:
- Nominal cover is under *3.5 Reinforcement* (clause F).
- The sampling-frequency table sits in Part 3, far from the materials sections.

**Decision:** add a *localization* step that finds the relevant parts first, then runs extraction only on those parts. It must work on documents written by different authors, with different numbering and layouts.

---

## Stage 3 – Parsing with PyMuPDF4LLM

PyMuPDF4LLM converts the PDF to Markdown, which keeps headings and tables. It took ~25 s and produced ~128,000 characters.

**What worked:** most headings, nested clauses (A / B / 1 / 2) and most tables came through, and the Table 5–7 values were correct.

**Issues found:**

- **Headings detected inconsistently.** In the PDF, 2.5 and 2.6 look identical (same size, bold), but they came out differently:
  ```markdown
  ### **2.5 CEMENT MATERIALS**
  ...
  5. Portland pozzolana cement (calcined clay based) conforming to IS 1489 (Pt –2)
  6. Sulphate resisting Portland cement conforming to IS 12330

  - **2.6 WATER**
  ```
  2.6 follows a numbered list (items 1–6), so the parser most likely treated it as list item 7. The same thing happened to 2.11, 3.6, 1.1–1.7 and 3.2–3.4. Any heading-based search would miss these sections.
- **Repeated page header and footer.** "SOM INDIA LLC 14 WALL STREET…" and the copyright line appear on every page, sometimes in the middle of a clause.
- **Table errors.** The Table 6 header text was split across columns. In Table 7, the chlorides and suspended-matter rows were merged into one row.
- **Unneeded OCR.** RapidOCR ran on pages 5, 25, 27, 33 and 50 even though the PDF is digital.

pdfplumber (the original parser) also produced a garbled sampling table (see Stage 4).

---

## Stage 4 – Switching to Docling

Docling was run locally (it could not be tested in a cloud sandbox because its model download was blocked).

**Improvements over PyMuPDF4LLM:**
- Every section heading is a proper `##` heading, including 2.6, 2.11, 3.6, 1.1–1.7 and 3.2–3.4:
  ```markdown
  ## 2.6 WATER
  ```
- Table 5 values are correct, with the plain/reinforced concrete headings kept.
- The Table 6 header stays whole, with the soil and groundwater groupings intact.
- Table 7 is correct, with chlorides and suspended matter as separate rows:
  ```markdown
  | Chlorides (as C1)  | 2000 mg/l for plain concrete work and 1000 mg/l for reinforced concrete work |
  | Suspended matter   | 2000 mg/l                                                                    |
  ```
- The page header/footer appears only twice (it was on every page in PyMuPDF4LLM's output).

**Remaining issues:**
- **Table captions are not always headings.** The Table 8 title comes out as plain text, so a heading-based search would miss it:
  ```markdown
  TABLE - 8 LIMITS OF DELETERIOUS MATERIALS (AGGREGATES) [IS 383 - Table 1]
  ```
- **Image markers.** There are 102 `<!-- image -->` markers that need stripping.
- **Stacked cell values in Table 6.** `330 kg/m³ 310 kg/m³` and `0.50 0.50` are still in one cell (same as PyMuPDF4LLM).
- **The sampling table appears twice, and the first copy is garbled.** In the first copy, "1" and "5 cu.m." merged:
  ```markdown
  | Up to 5 cu.m. in a day | 15 cu.m. to 15 cu.m.  | 2 |
  ```
  The second copy is correct:
  ```markdown
  | Up to 5 cu.m. in a day | 1 |
  | 5 cu.m. to 15 cu.m.    | 2 |
  ```
  Extraction should prefer the clean copy, or check both.

**Decision:** use Docling as the parser. Because the viva runs on localhost, its size is not a problem.

---

## Stage 5 – Designing localization *(in progress)*

**Options considered:**

| Option | Idea | Drawback |
|---|---|---|
| Keyword search | Find lines with parameter terms + values/units | Depends heavily on the chosen keywords; noise from common words |
| LLM reads every chunk | Cheap model classifies each chunk as relevant or not | Still processes the whole document (~32k tokens), slow under rate limits, may vary between runs |
| LLM reads only the headings | One small call (~1–2k tokens) picks relevant sections | Misses small clauses under unrelated headings (e.g. cover) |
| Embedding retrieval | Similarity search per parameter group | Extra model or API; not tried |

**First keyword test** (quick draft on the PyMuPDF4LLM output): it kept 21% of the document (~6,000 tokens), but found nothing for cement content and standard deviation, probably because those values sit inside tables.

**Current direction:** with Docling's reliable headings, localize mainly by **heading detection**, plus separate **table detection**. A table can be recognised by its Markdown rows (`| … |`), and the line just above it can be taken as its caption. This should keep real tables while ignoring sentences that only mention one (e.g. "as per Table 6"). *(not verified yet)*
