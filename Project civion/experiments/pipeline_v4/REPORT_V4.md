# Pipeline v4 - one Gemini call on the whole document (BLR only)

## 1. What was built
Folder `experiments/pipeline_v4/` (branch `pipeline-localization`). v1, v2, `auditor.py`, `database.py`,
`verify.py`, `table_reader.py` and the app are unchanged.

```
docling_output.md --(v2 clean.py + table padding squeezed, no LLM)--> doc.md (112,675 chars)
   --> ONE Gemini call: whole document + only the 34 extracted fields of database.PARAMETERS
   --> to_contract(): existing extraction contract (+ "field_info" beside it)
   --> grading tables: model maps columns, Python reads cells (tables_v4.py)
   --> quote check (verify.py) + location check --> auditor.run_civion_audit (unchanged)
```

| File | What |
|---|---|
| `pick_models.py` | lists the key's models, writes `models_config.json` |
| `models_config.json` | main `gemini-3.8-flash` (exact "Gemini 3.8 Flash"), lite `gemini-3.5-flash-lite`; free-tier limits |
| `gemini_call.py` | key from `Project civion/.env` (never printed), per-model limiter (req/min, input tokens/min, seeded from the log), retries on 429 / 5xx / dropped connection with backoff, per-day budget, every attempt logged |
| `call_log.jsonl` | one line per attempt: timestamp, model, input / output / reasoning tokens (API `usage_metadata`), wall time, status |
| `prompt_v4.py` | system prompt; per-field rules taken from `pipeline/groups.py`, shared rules from `prompt_rules.py` |
| `tables_v4.py` | finds a grading table in the whole document by the column headers the model names, then reads cells with the unchanged `table_reader.read_table` |
| `run_v4.py` | runner (`--role lite|main`, `--tables python|model`, `--from-raw` re-post-processes a saved answer without a call) |
| `compare_v4.py`, `check_tables_v4.py` | adapted copies of `shapes/compare_runs.py` and `shapes/check_tables_blr.py` that read v2 or v4 folders |
| `compare_main.md` | generated: v2 run4 vs v4 main1 vs v4 main2 (field by field, quotes, tokens) |
| `output/<run>/` | `doc.md` (text sent), `prompt_system.txt`, `response.json` (raw answer), `extraction.json`, `audit.json`, `quote_check.json`, `location_check.json`, `run_stats.json` |

Contract: field names from `database.PARAMETERS`; single value plain, range `[low, high]`; references in
`cross_references`; null when not found; tables `{group: {item: value}}` with IS 383 names; chemical basis kept
in the value ("500 as SO4"); `source_quotes`, `remarks`. Exposure and concrete type are stamped from the CLI
(not extracted). v4 extras: `field_info: {field: {type, location}}`, removed before the audit.
Formwork fields are not in `database.PARAMETERS`, so they are not asked for (set null, as in v2). The three site
SO3 fields are in `PARAMETERS` and are now asked for (v2 forced them null).

## 2. Runs (all BLR, exposure Moderate, Reinforced Concrete)
| Run | Model | Prompt | Tables | Input / output / reasoning tokens | Wall (successful attempt) | Quotes found / not |
|---|---|---|---|---:|---:|---:|
| lite1 | 3.5 Flash Lite | first | python | 29,788 / 4,122 / 0 | 10.0 s | 20 / 6 |
| lite2 | 3.5 Flash Lite | + no IS knowledge, options tables, quote example, member_covers refs | python | 30,003 / 4,303 / 0 | 10.7 s | 21 / 5 |
| lite3 | 3.5 Flash Lite | + water-table quote note (final prompt) | python | 30,045 / 4,137 / 0 | 23.4 s | 18 / 6 |
| lite_cells | 3.5 Flash Lite | final | model copies cells | 30,028 / 5,707 / 0 | 11.3 s | 17 / 8 |
| **main1** | 3.8 Flash | final | python | 30,045 / 4,323 / 7,920 | 226 s | **25 / 0** |
| **main2** | 3.8 Flash | final | python | 30,045 / 4,419 / 8,875 | 361 s | **24 / 0** |
| main_cells | 3.8 Flash | final | model copies cells | 30,028 / 6,772 / 8,134 | 229 s | 24 / 0 |

Prompt iteration was done on Flash Lite only. Lite fixes that carried over: lite1 took the grade (M25) from the
document's list of all grades and missed the "cover as specified in the Drawings" reference; lite2 fixed both.
Lite never wrote the header line of the water-quality table quotes (5 quotes rejected in every Lite run); the
main model always did.

## 3. v4 (main1, main2) vs v2 run4 - per field
Full table: `compare_main.md`. Audit recomputed with the current auditor for all runs.

| | v2 run4 | v4 main1 | v4 main2 |
|---|---:|---:|---:|
| Audit counts (pass / fail / warning; refs in pass) | 20 / 5 / 19; 6 | 22 / 5 / 17; 3 | 22 / 5 / 17; 3 |
| Fields with a value AND a verbatim quote | 16 | 21 | 21 |
| Quotes not found | 0 | 0 | 0 |

**Works in v4 (value + verbatim quote in BOTH main runs, 21):** cement_type, specified_min_cement,
specified_wc, mixing_time_minutes, transport_time_minutes (value differs, see 4), compaction_method,
curing_days, specified_slump_mm, water_ph, the five water_*_mg_l, measured_chloride_content,
aggregate_deleterious_limits, coarse / fine / all_in_aggregate_grading, sampling_cube_size_mm,
sampling_frequency. member_covers is a REFERENCE (-> drawings) in both runs, as in v2.

**Gained vs v2 run4 (5):** measured_chloride_content 0.6 kg/m3 (admixtures clause, MISSING -> PASS);
sampling_cube_size_mm 150 (MISSING -> PASS); coarse 42/42, fine 28/28, all-in 11/11 grading cells
(v2 run4: REFERENCE to IS 383 only -> PASS, every cell checked by `check_tables_v4.py`).
**Lost vs v2 run4: none.**

Other differences: specified_wc v2 0.55 (first in document order) vs v4 [0.5, 0.52] (mix-design clause, the
groups.py rule), both with a remark naming both values, FAIL either way (IS max 0.50). sampling_frequency: v2
took the copy with typing errors (2 samples up to 5 m3), v4 took the complete copy in section 3.10 and says so in
a remark; PASS in both. Deleterious limits 18/18 cells in all runs.

Still MISSING in both v2 and v4 (no value in BLR as far as the runs show; not re-checked by hand): the three site
SO3 values, freezing_thawing_exposure, specified_grade (BLR only lists all grades), specified_max_cement,
specified_sigma, specified_characteristic_strength, fire_resistance_rating, measured_so3_percent,
total_volume_m3, specified_sampling_sets.

Location (`field_info.location`): 22/22 heading paths found in the document in main1, 20/22 in main2 (the two
misses join two consecutive heading lines "TABLE - 10" + "GRADING OF FINE AGGREGATES" into one segment).

## 4. Consistency (main1 vs main2, same prompt and document)
Same value in 35 of 38 fields; same audit status in **38 of 38**.
- transport_time_minutes 30 vs 90: BLR states both "placed in position within 30 minutes from the time it is
  produced" and a mixing/delivery time of "11/2 hrs." (reduced in hot weather). Both runs name both values in a
  remark. Not a reading error; the field definition is ambiguous for this document (open question 1).
- water_ph [6.0, 9.0] vs [6, 9]; sampling_frequency first band from 0 vs 1 m3: formatting only.
Temperature was left at the model default (Gemini 3 guidance), so some variation is expected.

## 5. Wide table (BLR's 11-column coarse grading table)
v2 (LLM copying cells from routed excerpts) shifted columns: 29/38 cells right; v2 then moved to "model maps
columns, Python reads cells" (run4_reader: 42/42).
v4, whole document in one call:
- python mode (default; main1, main2, lite1-3): 42/42 coarse, 28/28 fine, 11/11 all-in in every run.
  `tables_v4.py` finds the table by its column headers (no unit ids in v4).
- model mode (Gemini copies the cells): lite_cells 42/42, 28/28, 11/11; main_cells 42/42, 28/28, 11/11
  (all 24 quotes found, audit counts identical to main1/main2).

With the whole document, Gemini did not shift columns in either mode (one run each; v2's shift came from
excerpts + a smaller model). Python mode stays the default: same result, the quote is built from the
document's own lines, and it costs fewer output tokens (main_cells 6,772 vs 4,323-4,419).

## 6. Tokens and wall time (MEASURED: API usage fields; format of report_v2.md section 7)
| Metric | v2 run4 | v4 main1 | v4 main2 |
|---|---:|---:|---:|
| Model | openai/gpt-oss-120b | gemini-3.8-flash | gemini-3.8-flash |
| API calls | 20 | 1 | 1 |
| Input (prompt) tokens | 62,722 | 30,045 | 30,045 |
| Output tokens (answer) | 14,312 (incl. hidden reasoning) | 4,323 | 4,419 |
| Reasoning tokens | not reported | 7,920 | 8,875 |
| **Total tokens** | **77,034** | **42,288** | **43,339** |
| Largest single call (total) | 5,108 | 42,288 | 43,339 |
| 429 / 5xx retries, final invocation only (see below) | 0 | 3 (503) | 3 (503) |
| Call errors | 0 | 0 | 0 |
| Wall time of the successful attempt (s) | - | 226 | 361 |
| Wall time of the call incl. retries and backoff (s) | 1,138 (sum of 20 calls) | 311 | 441 |
| Whole run wall time (s) | 1,140 | 312 | 442 |

Wall-time definition used everywhere in this report (tables in sections 2 and 6, `compare_main.md`):
"successful attempt" = the one request that returned the answer (from `call_log.jsonl`;
`run_stats.json` `call.ok_attempt_wall_s`); "incl. retries" = `call.wall_s`. main_cells: 229 s / 314 s.
**The retry row counts only the invocation that produced the saved run.** Earlier invocations that also hit
503s are in `call_log.jsonl` and listed in section 7.

Per step (input / output incl. reasoning, calls): v2 run4 = section picking 2,171 / 2,937 (1), routing
15,668 / 4,779 (5), extraction 44,883 / 6,596 (14); v4 = one extraction call 30,045 / 12,243 (main1),
30,045 / 13,294 (main2).
Main calls are slow: 226-361 s for one call, of which the model's thinking is most (7.9-8.9k reasoning
tokens), plus 70-85 s of 503 backoff in the final invocation of each run. Flash Lite: 10-23 s, no reasoning tokens.
main1's whole-run time (312.36 s) was overwritten by a later `--from-raw` re-post-process and restored by hand
from the console output; `run_v4.py` now keeps it (noted in `run_stats.json`).

## 7. Failures and problems seen
1. **503 "model is currently experiencing high demand"** on gemini-3.8-flash, 18 in total in `call_log.jsonl`:
   main1 9 (a first invocation made 6 and gave up after its 5 retries, 373 s, saved nothing; the second made 3
   and succeeded), main2 3 (after the dropped connection below), main_cells 3. Backoff 10/20/40 s. The first
   main1 invocation's console output was not saved; its attempts are only in the log. 503s are not counted
   against the daily budget.
2. **Dropped connection**: main2's first attempt ended after 205 s with "Server disconnected without sending a
   response" (no HTTP code), which the first version did not retry. Now retried; that attempt is counted against
   the budget (it may have run on the server). Log: `output/main2_attempt1_disconnected.log`.
3. **Flash Lite** writes table quotes as the data row only (water table, Table 5 row) and once used the column
   numbering row "(1) | (2) ..." as the header: rejected by verify.py. Values themselves were right. Lite also
   took the hot-weather transport time (75 min) in lite1 and lite2.
4. **verify.py and multi-line text quotes**: verify.py treats any multi-line quote as a table quote. main1's
   curing quote is two verbatim sentences on two lines and was marked "not found". v4 adds one rule on its own
   side (verify.py unchanged): a multi-line quote with no "|" is checked line by line as text.
5. Daily budget used today: main 4 of 20 counted (main1, main2 dropped attempt, main2, main_cells), Lite 5.

## 8. Open questions (for the owner / planner)
1. transport_time_minutes on BLR: 30 min (placing after production) or 90 min (mixing/delivery time)? The
   groups.py rule says "time from mixing/production to placing (transport/delivery)", which fits both.
2. specified_wc: v4 follows the groups.py rule (mix-design clause wins -> [0.5, 0.52]); v2 run4 audited 0.55.
   Which should the audit use when both are stated?
3. The v4-side multi-line text-quote rule (section 7.4): keep it in v4, or move it into verify.py for all pipelines?
4. Main-model latency (4-7 min per document with retries) vs Flash Lite (10-25 s, same values except the quote
   format and one transport-time pick). Is Lite + a Python fix for one-line table quotes worth testing?
5. `Project civion/.env` was tracked by git. Done in the follow-up commit: untracked (`git rm --cached`; the file
   stays on disk) and a root `.gitignore` added. History checked: the only commit that ever contained `.env`
   (b8c9705, already on origin/main) holds a placeholder, no real Groq or Gemini key; no commit contains
   GEMINI_API_KEY. No key rotation is needed because of git. Still do not push before reviewing the branch.
6. An older interactive `experiments/pick_models.py` (untracked, not written in this work) exists; v4 uses
   `pipeline_v4/pick_models.py`. Delete the old one?
