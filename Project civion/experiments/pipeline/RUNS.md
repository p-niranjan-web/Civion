# Pipelines and runs (all on the BLR spec unless noted)

## Pipelines
- **v1** (result in `v1_results/`; BLR: 12 calls, 42k tokens)
  1. Clean (`clean.py`): Docling markdown -> strip image markers / repeated headers -> `clean.md` (136k chars).
  2. Split into sections at every heading (`sections.py`): 62 sections, 17 tables. No LLM.
  3. Pick sections - 1 LLM call (`localize.py`): only the list of headings is sent (~2k tokens); the LLM
     returns the relevant section ids, each tagged with a topic (materials / durability_grade /
     production_curing / cover_sampling). Parents added by rule -> `localized.md` (84k chars, 62 %).
  4. Chunks (`extract.py`, no LLM): per topic, sections in document order, cut so prompt + answer stays
     under ~5,000 tokens -> 11 chunks.
  5. Extract - 11 LLM calls: each sends ONE chunk + the FULL JSON schema (all fields) + rules; the LLM
     fills what it finds in that chunk, null otherwise.
  6. Merge (no LLM): per field, the value from a chunk whose topic owns the field (first in document
     order), else the first non-null from any chunk; all candidates kept.
  7. Audit (`auditor.py`) against `database.py`.
- **v2** (`route.py`, `extract_v2.py`; runs in `output_v2/<run>/`)
  1. Same section picking, plus safety nets that add sub-sections and sections with cue words.
  2. Sections are split into units (one clause or one table each).
  3. Routing calls tag each unit with the parameter groups it can feed (a unit may feed several).
  4. One extraction call per group: only THAT group's fields + only the units routed to it (batched if
     large). Groups are fixed and listed in `groups.py`.
- **v4** (folder `../pipeline_v4/`, Gemini; report `../pipeline_v4/REPORT_V4.md`; runs in `../pipeline_v4/output/<run>/`)
  1. Same cleaning as v1/v2 (`clean.py`), Docling table padding squeezed (113k chars). No section picking,
     no routing, no batching.
  2. ONE call: the whole document + only the fields of `database.PARAMETERS` (rules from `groups.py`).
  3. Grading tables: the model names the columns, Python finds the table and reads the cells.
  4. Quote check (`verify.py`) and audit (`auditor.py`) unchanged.
  BLR: 1 call, ~42k tokens (30k in); 21 fields with a verbatim quote vs 16 in v2 run4, none lost.

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

## v4 runs (`../pipeline_v4/output/`)
| Run | What it is |
|---|---|
| lite1, lite2, lite3 | prompt iteration on gemini-3.5-flash-lite (lite3 = final prompt) |
| lite_cells | final prompt, model copies the grading cells itself (Lite) |
| main1, main2 | final prompt on gemini-3.8-flash, twice, for consistency (35/38 same values, 38/38 same audit status) |
| main_cells | final prompt, model copies the grading cells itself (gemini-3.8-flash) |

Every API attempt: `../pipeline_v4/call_log.jsonl`. Comparison with v2 run4: `../pipeline_v4/compare_main.md`.
