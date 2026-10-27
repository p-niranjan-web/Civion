# Pipelines and runs (all on the BLR spec unless noted)

## Pipelines
- **v1** (`localize.py`, `extract.py`; result in `v1_results/`, 12 calls, 42k tokens)
  1. One LLM call sees only the heading outline, picks the relevant sections and tags each with a topic
     (materials / durability_grade / production_curing / cover_sampling).
  2. The picked text is packed by topic into chunks of at most ~5,000 tokens. Each call sends ONE chunk
     (not the whole scoped document) with the WHOLE JSON schema (all fields).
  3. Merge: per field, the answer from a call whose topic owns that field wins; all candidates are kept.
- **v2** (`route.py`, `extract_v2.py`; runs in `output_v2/<run>/`)
  1. Same section picking, plus safety nets that add sub-sections and sections with cue words.
  2. Sections are split into units (one clause or one table each).
  3. Routing calls tag each unit with the parameter groups it can feed (a unit may feed several).
  4. One extraction call per group: only THAT group's fields + only the units routed to it (batched if
     large). Groups are fixed and listed in `groups.py`.

## v2 runs (`output_v2/`)
| Run | What it is |
|---|---|
| run1 | first v2 run (cross-reference prompt wording differed; found 0 references) |
| run2 | v2 baseline - the "before" for the shapes work |
| run3 | first run after the shapes change (new aggregates group, ranges, remarks, references, two-line table quotes) |
| run4 | final BLR run with the shapes code (used in CHANGES_SHAPES.md) |
| nmp1 | NMP Noida attempt - failed at section picking (Groq error); nothing extracted |

## Partial re-runs (only some groups, reusing a run's units and routing)
| Folder | Purpose |
|---|---|
| table_quotes_check | test of the header-row + data-row table quote (durability, materials) on run2 |
| run3_tables | aggregates retries on run3 (cell listing / one field per call; did not fix coarse grading; ended in connection errors) |
| run4_reader | test of the Python table reader on run4 (coarse 42/42, fine 28/28, all-in 11/11) |

Token use per run and step: `report_v2.md` section 7. Logs: `output_v2_<run>.log`.
