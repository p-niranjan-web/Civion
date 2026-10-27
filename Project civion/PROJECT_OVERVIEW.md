# CIVION — project overview (for anyone/any AI picking this up)

This file explains what the software is trying to do and how the pieces fit together, so a
new contributor (human or AI) can get oriented without re-deriving it from the code. For
setup/run instructions, see `README.md` at the repo root. For a list of currently-known
issues, see `KNOWN_ISSUES.md` in this folder — that file is a findings list only; nothing
in it should be acted on without the repo owner's explicit go-ahead.

## What this software is for

CIVION checks whether a construction technical specification document (a PDF a structural
engineer or contractor writes for a project) actually complies with **IS 456:2000**, the
Indian standard code of practice for plain and reinforced concrete. A user uploads a spec
PDF, picks (or answers a short questionnaire to derive) the project's environmental
exposure condition, and CIVION:

1. Extracts the concrete-related values the spec document actually states (grade, cement
   content, water-cement ratio, curing days, cover, sampling frequency, etc. — around 40
   parameters total) into structured JSON.
2. Runs those extracted values through a compliance audit against the real IS 456
   requirements for the given exposure/concrete-type combination.
3. Produces a pass/fail/warning ledger with traceability back to the exact quote in the
   source document that each extracted value came from.
4. Lets the user chat about the results, and optionally generates a "rectified" version of
   the specification that would pass.

**The important design point:** the spec document being audited is the *test input*, not
the source of truth. It is expected to sometimes be wrong — that's the whole reason the
tool exists. The source of truth for what IS 456 actually requires is hardcoded in
`database.py`. Don't treat disagreements between a sample spec doc and `database.py` as
evidence that `database.py` needs to be corrected — that's usually the audit engine
correctly doing its job. (If you're evaluating whether the audit logic itself is *correct*,
compare its behavior to real IS 456 knowledge, not to whatever a sample test document says.)

## How the pieces fit together

```
Project civion/
├── api/main.py     FastAPI backend — /api/audit, /api/chat, /api/optimize, /api/report/*
├── parser.py       Step 1: PDF text extraction, then a single Groq LLM call that turns
│                   the spec document's text into the structured JSON auditor.py expects.
│                   Also detects/derives exposure class + concrete type when needed.
├── auditor.py      Step 2: run_civion_audit(user_data, is456_rules) — the actual
│                   compliance-check logic. Pure function, no LLM calls, no I/O. Takes the
│                   parsed JSON + IS456_MASTER and returns {counts, ledger, traceability}.
├── database.py     IS456_MASTER — the hardcoded ground-truth IS 456 tables (durability
│                   requirements, sulphate attack classes, nominal cover, sampling
│                   frequency, formwork striking times, etc). Also EXTERNAL_CODE_REFERENCES
│                   for cross-references to other IS codes (e.g. IS 383 for aggregates).
├── config.py       Groq client setup, GROQ_API_KEY / GROQ_MODEL from environment/.env
├── downloads/cache/  Deterministic cache of parser output, keyed by file hash (+ exposure
│                   + concrete type, since re-running with a different exposure shouldn't
│                   reuse a stale extraction)
└── frontend/       React + Vite SPA — upload, exposure selector, dashboard, ledger,
                    traceability view, chat, optimization/rectified-spec generation
```

The **only place compliance logic lives** is `auditor.py` + `database.py`. Everything else
(parser, API, frontend, chatbot) exists to get data into that function and present its
output. If you're asked to work on "the compliance check," that's these two files; if
asked about "the chatbot," that's `api/main.py`'s chat endpoint plus the frontend chat
component, which grounds its answers in the audit's own output rather than re-deriving
compliance logic itself.

## Things worth knowing before touching this codebase

- **Exposure and concrete type are often supplied externally, not extracted.** The frontend
  has an exposure selector (direct pick, or a 6-question wizard that derives the class) and
  a concrete-type hint. When set, these are stamped onto the parsed JSON *after* extraction,
  overriding whatever the LLM guessed — see `parser.py`'s `detected_exposure` /
  `detected_concrete_type` handling. This matters because many spec documents state their
  requirements as a table keyed by exposure class + concrete type (not a single number), so
  the extraction prompt has explicit "table resolution" instructions to pick the right
  row/column once the exposure/type is known externally.
- **The Groq model is configurable and has broken silently before.** `config.py`'s
  `GROQ_MODEL` defaults to `openai/gpt-oss-120b`; a prior default model was decommissioned
  by Groq and every extraction silently returned nothing until this was caught. If
  extraction stops working, check whether the configured model still exists on the account.
- **The parser cache is deterministic and keyed by file hash + exposure + concrete type** —
  re-running the same PDF with the same exposure/type will not re-call the LLM. Delete the
  relevant file (or the whole `downloads/cache/` folder) to force re-extraction.
- **`auditor.py` is designed to be run standalone** — it takes plain dicts and returns plain
  dicts, no framework dependencies. This makes it straightforward to test compliance logic
  directly (construct a `user_data` dict by hand, call `run_civion_audit(user_data,
  IS456_MASTER)`, inspect the returned ledger) without needing a running server or an LLM
  call at all.
