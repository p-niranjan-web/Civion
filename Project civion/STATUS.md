# Civion work status (updated by Claude Code)

Last update: 2026-10-27, end of Part 3

## State: DONE - waiting for your answers to 7 open questions (nothing running)

Progress: 100 % of what was agreed (NMP run skipped, as you decided).

## Read these
- Final report: experiments/shapes/CHANGES_SHAPES.md
- Parameter x document list: experiments/shapes/doc_coverage.md
- Tokens v1 / v2 / v2-shapes (input/output per step): experiments/pipeline/report_v2.md section 7

## Results in one line each
- 40/40 hand-built audit tests pass; all existing parameters behave as before (one sampling bug fixed).
- BLR run4: 20 pass, 5 fail, 19 missing, 6 references; 20/20 quotes verified in the document.
- Aggregates: deleterious limits work (18/18). Fine/all-in grading worked in run3, gave REFERENCE in run4.
  Coarse grading (11-column table) is misread by the LLM - not working.

## Waiting for your reply on (details in CHANGES_SHAPES.md, "Open questions")
1. Build a Python table reader for wide tables (LLM only picks the table)?
2. Prompt: extract the table when a doc has both a table and "as per IS 383"?
3. References to non-IS codes (BS, ASTM): keep as pass, or warn?
4. Build the "extras" list (unaudited requirements, collapsed UI section)?
5. Curing with PPC/PSC = 10 days (IS 456 cl 13.5.1)?
6. Old known issues (#2, #3, strength check) - leave for now?
7. App's Groq client has the same TLS timeout on this network - add the workaround there too?
