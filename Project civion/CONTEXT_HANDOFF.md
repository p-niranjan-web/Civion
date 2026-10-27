# CIVION — context handoff

Purpose of this file: give another LLM (or a new human contributor) enough context to be
useful on this project from a cold start, without reading any code first. It summarizes
what the software does, what work has been done, what's currently known to be broken, and
what's next. For architecture/file-layout detail, see `PROJECT_OVERVIEW.md` in this same
folder — this file is the narrative/history version; that one is the structural reference.

## What CIVION is

CIVION checks whether a construction technical specification document (a PDF written by a
structural engineer or contractor) complies with **IS 456:2000**, the Indian standard code
of practice for plain and reinforced concrete. A user uploads a spec PDF, provides (or
derives via a guided questionnaire) the project's environmental exposure class, and the
tool:

1. Extracts ~40 concrete-related parameters from the document (grade, cement content,
   water-cement ratio, curing days, cover, sampling frequency, etc.) into structured data.
2. Runs those values through a compliance check against the real IS 456 requirements for
   the given exposure class / concrete type.
3. Produces a pass/fail/warning ledger, each item traceable back to the exact quote in the
   source document it came from (see "Traceability / source quoting" below for how this
   actually works).
4. Lets the user chat about the results, and can generate a "rectified" version of the spec
   that would pass.

**Who it's for:** the person who *wrote* the spec document (the engineer/contractor), as a
pre-submission self-check before they finalize and submit it — not a third-party auditor
reviewing someone else's work.

**Core design principle:** the uploaded spec document is the *test input*, expected to
sometimes be wrong — that's the entire point of the tool. The source of truth for what IS
456 actually requires is a hardcoded dataset in the codebase, independent of any sample
document. When a sample spec document disagrees with that hardcoded dataset, that's usually
the tool correctly catching a real error in the document — not evidence the dataset needs
"correcting" to match the sample.

## How it's put together (conceptual, no code)

- A **parsing stage** reads the PDF and uses an LLM (via Groq) to turn its text into
  structured data matching what the compliance engine expects. This stage also handles
  detecting/deriving exposure class and concrete type when the user didn't set them
  directly.
- A **compliance engine** (pure logic, no LLM calls, no I/O) takes the structured data plus
  the hardcoded IS 456 reference dataset and produces the pass/fail/warning ledger. This is
  the one place all compliance logic lives — everything else exists to feed this stage or
  present its output.
- A **hardcoded reference dataset** encodes the real IS 456 tables (durability
  requirements, sulphate attack classes, nominal cover, sampling frequency, formwork
  striking times, etc.), plus cross-references to other IS codes (e.g. IS 383 for
  aggregates).
- A **backend API** exposes audit, chat, optimize, and report endpoints.
- A **caching layer** avoids re-running the LLM extraction for a PDF it's already seen with
  the same exposure/concrete-type combination.
- A **frontend SPA** handles upload, the exposure questionnaire, and displays the
  dashboard/ledger/traceability/chat.

## Traceability / source quoting

Every extracted parameter is expected to come with an exact quote from the source PDF
proving where it was found — this is what lets the ledger say "here's the value we checked,
and here's the sentence/row/cell in your document it came from," not just a bare pass/fail.

- The extraction step is instructed (as part of its prompt) to return, alongside every
  non-null extracted field, a parallel map of that field name to the exact quote in the
  document text that justifies it — including quoting the specific table row/cell text when
  a value was resolved from a table keyed by exposure class or concrete type.
- Cross-references to other codes (e.g. "aggregate grading deferred to IS 383") are quoted
  the same way — each cross-reference carries its own exact source quote alongside which
  requirement is being deferred and which code it's deferred to.
- The compliance engine consumes this quote map and attaches the matching quote to each
  ledger entry it produces, falling back to a "No quote extracted" placeholder if a quote is
  missing for a given field. It builds a separate parallel structure (parameter name →
  extracted value → source quote) alongside the pass/fail ledger itself.
- Exposure class and concrete type are a special case: when the user supplies these directly
  (via the exposure selector/questionnaire or the concrete-type picker) rather than letting
  the LLM infer them from the document, the system still records a quote for them — an
  auto-generated one noting that the value was user-specified rather than a quote from the
  document text — so these two fields still show up in the traceability view instead of
  appearing quote-less.
- Known gap: quoting is only as reliable as the extraction step producing an honest quote for
  every field it fills in; this hasn't been separately audited for accuracy (e.g. whether a
  quote is ever fabricated or mismatched to its value) the way the compliance-check logic in
  `KNOWN_ISSUES.md` has been. Worth treating as an open question, not a verified-correct
  feature, if traceability accuracy specifically becomes a concern.

## Other features (not yet covered above)

- **Downloadable PDF report**: the ledger and traceability tables can be exported as a
  branded PDF (logo, pass/fail/warning summary counts in color, a compliance-ledger table,
  and a separate "Engineering Traceability" table listing parameter / extracted value /
  source quote per row) — a snapshot of the audit a user can save or hand off, not just an
  on-screen view.
- **Rectified/optimized specification workflow**: the user can adjust individual flagged
  values (e.g. bump a non-compliant cement content up to the passing minimum) and the system
  re-runs the exact same compliance engine against the adjusted values, computes a new
  pass-percentage score, and can export a second PDF that compares the original vs. adjusted
  ledger side by side — with any value that actually changed highlighted in green. This is
  how the tool gets the user from "here's what's wrong" to "here's a version that would
  pass," without the LLM inventing new compliance logic — it's the same audit engine, just
  re-run on edited input.

## Work completed so far

- **Exposure questionnaire logic**: built a 6-question guided wizard that derives the IS
  456 exposure class using a max-severity accumulation model (never downgrades once a more
  severe condition is indicated). Several ambiguities in the original spec for this wizard
  were resolved conservatively (escalate rather than guess low), since a wrong-low exposure
  class would weaken the whole audit.
- **Fixed a silent extraction failure**: the LLM model originally hardcoded for extraction
  had been decommissioned by the provider, so every extraction call was silently failing
  and the audit reported "nothing detected" for any document, with no error surfaced. The
  model is now configurable via environment/config rather than hardcoded, and the extraction
  was consolidated from 3 sequential LLM calls into 1 combined call — partly for speed,
  partly because 3 back-to-back calls were hitting the provider's rate limit and each retry
  added significant delay.
- **PDF parsing** was switched to a more capable extraction library after issues with the
  original approach.
- **Chatbot fix**: corrected Markdown/LaTeX rendering in the chat UI, and changed the
  chatbot to ground its answers in the full audit context/output rather than re-deriving
  compliance judgments on its own.
- **Concrete-type selector**: added a UI control for picking concrete type used in table
  lookups during extraction.
- **IS 383 cross-reference handling**: added recognition of cross-references to IS 383
  (aggregates) in the spec document; also removed an aggregate max-size check that had no
  verified basis.
- **`.env` handling**: fixed encoding issues and added support for configuring the Groq API
  key via a `.env` file.
- **Verification pass on the compliance engine**: did a systematic cross-check of the
  compliance-check logic against real IS 456 requirements (hand-built test inputs run
  directly through the compliance engine, independent of the LLM/PDF pipeline). Findings
  from this pass are recorded in `KNOWN_ISSUES.md`, not yet acted on — see below.

## Known issues (found, not yet fixed — see `KNOWN_ISSUES.md` for full detail)

`KNOWN_ISSUES.md` is explicitly a **findings list, not a task list** — nothing in it should
be implemented without the repo owner's explicit go-ahead, even if a fix looks small or
obvious. Summary of what's in it:

**Confirmed by directly running the compliance engine:**
1. Concrete type must match an exact expected string ("Plain Concrete" / "Reinforced
   Concrete"); any other value (e.g. the plausible abbreviation "RCC") silently falls back
   to generic default thresholds instead of flagging that the type couldn't be matched —
   demonstrated to let a genuinely non-compliant design pass.
2. Missing cement type / exposure fields report a false "Pass — must be defined", because
   the code supplies a default value before checking for presence, so the presence check
   can never actually fail.
3. The sulfate-attack "Class 2" requirement in the reference dataset incorrectly collapses
   two valid real options (OPC/PSC/PPC at one threshold, or SRC at a lower threshold) into
   one wrong composite — causing both a false Pass (cement content) and a false Warning
   (cement type) on a compliant OPC design.

**Found by code reading, high confidence, not yet reproduced live:**
4. Characteristic-strength acceptance check has a fabricated upper bound (real IS 456 has
   no upper cap — stronger-than-specified concrete should never fail) and doesn't match the
   actual clause's sample-group-mean formula.
5. Sampling-count formula has an off-by-one at exact 50 m³ multiples (stricter than
   required, not unsafe).
6. IS 383 cross-references are unconditionally marked Pass with no real numeric check
   against the reference dataset (which does hold the real reference numbers, but the
   compliance engine never reads them for this check — only the chatbot does).
7. Several checks hardcode their IS 456 limit as a literal number instead of reading the
   equivalent entry that already exists in the reference dataset for that exact purpose
   (transportation time, max cement content, water pH, sulphate content, cube size) — values
   currently agree, but the two copies can silently drift.
8. A workability/slump table exists in the reference dataset but is never actually used;
   the real check uses one flat range regardless of category.
9. Member cover is always checked against the Reinforced Concrete table regardless of the
   audited concrete type — no Plain Concrete alternative exists in the data (may be
   intentional; flagged to make it a deliberate decision).

**Explicitly checked and confirmed correct** (for reference): sampling-frequency
thresholds, formwork removal days, sulfate classes 1/3/4/5, chloride content limits by
concrete type, mixing time, compaction-method prohibition list, curing days by cement type.

## Future plans

There is no committed roadmap beyond fixing what's already found. The candidate next work,
in the repo owner's likely priority order pending their explicit approval, is the numbered
list above under "Known issues" — i.e., the next phase of work is expected to be resolving
those findings in `KNOWN_ISSUES.md`, starting with the three "confirmed live" items since
those have been directly demonstrated to produce wrong audit verdicts (items 1–3), before
moving to the "found by code reading" items (4–9). None of this should be started without
the repo owner explicitly signing off item-by-item — this file is context, not authorization.

## How to verify any of the above still holds

This file and `KNOWN_ISSUES.md` are point-in-time snapshots. Before acting on any specific
claim above (a bug, a file's behavior, a config default), re-verify against the current
state of the repository rather than trusting this summary — the compliance engine is
designed to be run standalone with hand-built input, which is the fastest way to confirm or
refute any of the "known issues" claims directly.
