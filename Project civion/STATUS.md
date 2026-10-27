# Civion work status (updated by Claude Code)

Last update: 2026-10-27 (during Part 3)

## State: WORKING - nothing needed from you yet

Progress: about 75 %

## Done and committed
- Part 1: REFERENCE status (backend + UI), table quotes = header row + data row (verify.py checks it).
- Part 2: catalogue of BLR requirement shapes (experiments/shapes/catalogue.md).
- Part 3:
  - Fixed transport time (no IS 456 limit) and workability bands (IS 456 cl 7.1).
  - database.py restructured: every audited parameter declares a shape; IS 383:2016 tables added
    (values typed from the IS 383 PDF, not from BLR).
  - auditor.py: one check per shape. 40/40 hand-built test cases pass.
  - Remarks (e.g. "w/c 0.55 in table vs 0.5-0.52 in mix clause") shown in the Ledger.
  - HOW_TO_ADD_PARAMETER.md at the repo root.

## Running now (SLOW - Groq limit)
- Re-extracting the aggregate tables from BLR (coarse grading came out with shifted columns; testing
  one-field-per-call extraction). 10 of 12 calls done.
- ISSUE: Groq free-tier usage limit reached; Groq now makes each call wait 14-30 min (daily token cap).
  Code is fine. Optional for you: a second Groq API key, or wait for the reset (usually within a day).

## Still to do
1. Check the aggregate re-extraction against BLR's own tables.
2. Run NMP Noida through the pipeline; write experiments/shapes/doc_coverage.md
   (parameter x document list).
3. Final report: experiments/shapes/CHANGES_SHAPES.md.

## Waiting for your reply on
- Nothing right now.
