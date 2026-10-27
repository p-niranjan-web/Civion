# Pipelines and runs (all on the BLR spec unless noted)

## Pipelines
- **v1** - clean -> sections -> one LLM call picks the relevant sections from the headings -> extraction in
  fixed batches over that text. Result kept in `v1_results/` (12 calls, 42k tokens).
- **v2** - same section picking, plus: sections split into units (clauses / tables) -> LLM routes each unit
  to parameter groups -> one extraction call per group (batched if large). Runs in `output_v2/<run>/`.

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
