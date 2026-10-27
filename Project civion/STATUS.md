# Civion work status (updated by Claude Code)

Last update: 2026-10-27, after your answers to the 7 open questions

## State: WAITING FOR YOU - nothing running

## Done since your answers
- Q1 Wide tables: DONE. The LLM only says which table and which column is which size; Python reads
  the cells. BLR: coarse grading 42/42 cells correct (before: 29/38), fine 28/28, all-in 11/11.
  All three PASS IS 383:2016. Commit a2b879b.
- Q2 Prompt fix: DONE (fill from the document's own table even if it also says "as per IS 383").
- Q3 Non-IS references stay PASS (no change).

## Waiting for your reply on (explained in the chat)
- Q4 "Extras": show requirements the document states that match none of our 37 parameters
  (e.g. placing temperature 35 C, free fall 1.5 m), in a separate, not-audited list? yes / no
- Q5 Curing: DONE (commit 245af57) - PPC/PSC = 10 days, dry hot weather = 10 days (IS 456 cl 13.5.1);
  dry hot weather itself is not asked from the user (ignored for now). 43/43 tests pass.
- Q7 App connection fix (only matters on networks where Groq calls time out): add to the app? yes / no
- Q6 is information only (no decision needed unless you want them fixed).
