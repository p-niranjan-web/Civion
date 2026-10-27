# Civion pipeline v2 - BLR report

Args: exposure=`Moderate`, concrete_type=`Reinforced Concrete`, target max tokens/call `5000`, model `openai/gpt-oss-120b`.

**MEASURED** = counted by code / Groq API `usage` field. **EST** = chars/4 estimate. v1 numbers come from `v1_results/` (the committed v1 run), not a re-run.

## Takeaways

- **Recall improved, as intended.** v2 finds 3 parameters that v1 missed: transport time 30 min, slump 35 mm, water pH 6.0. All three were in v1's localized text but lost in v1's long mixed-topic calls. v2 found them in both runs.
- **Cost went up, not down.** v2 used about 62-65k MEASURED tokens per run versus v1's 42k, and about 945 s versus 637 s. Routing alone is 5 calls / about 20k tokens, and "tag more when unsure" sends the materials group about 45 units / 11k EST tokens (5 calls). The ~1-minute gap between calls is the TPM pacer, not API latency.
- **Unique document text sent to extraction fell slightly** (62% -> 56-59%), but repeats across groups mean 88-100% of the document's size is sent in total.
- **Audit PASS counts are not comparable on their own.** The auditor gives PASS to every cross-reference, so v1's 11 cross-references (several of them ambiguous) inflate its PASS count. Real parameter outcomes: v1 found 11 values, v2 found 14. FAIL is 4 in all runs; these are true spec-vs-IS 456 differences.
- **Consistency:** extracted values were identical in run1 and run2. Stage A scope differed by 3 sections. 28% of common units got different routing tags, which changed where the chloride limit was routed.
- **Remaining gaps:** 2 routing misses (chloride limit, cube size), 1 unresolved conflict (w/c 0.55 vs 0.52), 1 ignored per-field rule (curing 7+7 days), 2 composed (non-verbatim) quotes, and the 1.7 hot-weather section still out of scope.

## 1. v1 vs v2 summary

| Metric | v1 | v2 run1 | v2 run2 |
|---|---:|---:|---:|
| API calls (MEASURED) | 12 | 19 | 18 |
| Prompt tokens, total (MEASURED) | 31,552 | 54,827 | 51,554 |
| Completion tokens, total (MEASURED) | 10,683 | 10,051 | 10,400 |
| **Total tokens (MEASURED)** | **42,235** | **64,878** | **61,954** |
| Largest single call, tokens (MEASURED) | 5132 | 5003 | 4771 |
| Calls over 5,000 tokens (MEASURED) | 1 | 1 | 0 |
| 429 retries (MEASURED) | 0 | 0 | 0 |
| Call errors | 0 | 0 | 0 |
| Wall time total, s (MEASURED, incl. TPM pacing sleeps) | 637 | 942 | 947 |
|   of which extraction step, s | 628 | 619 | 624 |
| Whole doc (clean.md), chars | 136,124 | 136,124 | 136,124 |
| Chars sent to extraction calls (incl. repeats) | 84,282 (62%) | 136,020 (100%) | 120,235 (88%) |
| Unique doc chars sent to extraction | 84,282 (62%) | 80,089 (59%) | 76,378 (56%) |
| Parameters found (of 28: 26 params, covers counted per member) | 11 | 14 | 14 |
| Cross-references | 11 | 0 | 6 |
| Audit PASS | 21 | 13 | 19 |
| Audit FAIL | 4 | 4 | 4 |
| Audit MISSING | 25 | 22 | 22 |
| Audit WARNING | 0 | 0 | 0 |
| Source quotes not found in clean.md (deterministic check) | - | 0 | 2 |

v1's quote check (run afterwards with verify.py): 1 quote not in the document (`concrete_type`, model-written; fixed in v2).

## 2. Calls (MEASURED usage)

**v1**

| Call | effort | Prompt | Completion | Total | Text chars | Units | Retries | Wall s | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| localize | medium | 2171 | 2961 | 5132 | - | - | 0 | 7.46 |  |
| extract[0] materials | low | 2595 | 1041 | 3636 | 6275 | - | 0 | 63.2 |  |
| extract[1] materials | low | 3050 | 798 | 3848 | 9096 | - | 0 | 62.73 |  |
| extract[2] materials | low | 2022 | 491 | 2513 | 9219 | - | 0 | 62.43 |  |
| extract[3] materials | low | 2639 | 509 | 3148 | 7184 | - | 0 | 1.62 |  |
| extract[4] durability_grade | low | 2544 | 758 | 3302 | 8912 | - | 0 | 62.71 |  |
| extract[5] production_curing | low | 3265 | 463 | 3728 | 9104 | - | 0 | 62.13 |  |
| extract[6] production_curing | low | 1937 | 681 | 2618 | 3496 | - | 0 | 62.44 |  |
| extract[7] production_curing | low | 2861 | 1147 | 4008 | 7639 | - | 0 | 63.46 |  |
| extract[8] production_curing | low | 2906 | 738 | 3644 | 8224 | - | 0 | 62.62 |  |
| extract[9] cover_sampling | low | 2881 | 489 | 3370 | 8133 | - | 0 | 62.03 |  |
| extract[10] cover_sampling | low | 2681 | 607 | 3288 | 6707 | - | 0 | 62.12 |  |

**v2 run1**

| Call | effort | Prompt | Completion | Total | Text chars | Units | Retries | Wall s | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| localize | medium | 2171 | 2832 | 5003 | - | - | 0 | 6.72 |  |
| route[0] | low | 3221 | 1034 | 4255 | - | 27 | 0 | 62.94 |  |
| route[1] | low | 3500 | 859 | 4359 | - | 26 | 0 | 62.85 |  |
| route[2] | low | 3109 | 1008 | 4117 | - | 28 | 0 | 63.7 |  |
| route[3] | low | 3016 | 977 | 3993 | - | 27 | 0 | 62.92 |  |
| route[4] | low | 2423 | 588 | 3011 | - | 19 | 0 | 62.03 |  |
| extract[grade_strength#0] | low | 2661 | 119 | 2780 | 8855 | - | 0 | 0.76 |  |
| extract[durability#0] | low | 2900 | 341 | 3241 | 12316 | - | 0 | 61.82 |  |
| extract[durability#1] | low | 3320 | 116 | 3436 | 12260 | - | 0 | 61.1 |  |
| extract[durability#2] | low | 3380 | 294 | 3674 | 11733 | - | 0 | 61.92 |  |
| extract[materials#0] | low | 2963 | 167 | 3130 | 9774 | - | 0 | 61.21 |  |
| extract[materials#1] | low | 3263 | 419 | 3682 | 12622 | - | 0 | 62.13 |  |
| extract[materials#2] | low | 2411 | 111 | 2522 | 7886 | - | 0 | 61.57 |  |
| extract[materials#3] | low | 1917 | 168 | 2085 | 11357 | - | 0 | 61.57 |  |
| extract[materials#4] | low | 3016 | 110 | 3126 | 10313 | - | 0 | 1.51 |  |
| extract[production#0] | low | 3643 | 230 | 3873 | 12918 | - | 0 | 61.63 |  |
| extract[production#1] | low | 3476 | 419 | 3895 | 12555 | - | 0 | 62.23 |  |
| extract[production#2] | low | 933 | 79 | 1012 | 1157 | - | 0 | 1.41 |  |
| extract[cover_sampling#0] | low | 3504 | 180 | 3684 | 12274 | - | 0 | 60.14 |  |

**v2 run2**

| Call | effort | Prompt | Completion | Total | Text chars | Units | Retries | Wall s | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| localize | medium | 2171 | 2600 | 4771 | - | - | 0 | 7.07 |  |
| route[0] | low | 3125 | 828 | 3953 | - | 26 | 0 | 62.61 |  |
| route[1] | low | 3500 | 910 | 4410 | - | 26 | 0 | 62.95 |  |
| route[2] | low | 3109 | 941 | 4050 | - | 28 | 0 | 62.94 |  |
| route[3] | low | 3016 | 977 | 3993 | - | 27 | 0 | 62.77 |  |
| route[4] | low | 2423 | 730 | 3153 | - | 19 | 0 | 62.72 |  |
| extract[grade_strength#0] | low | 2370 | 91 | 2461 | 7361 | - | 0 | 0.76 |  |
| extract[durability#0] | low | 3193 | 429 | 3622 | 11780 | - | 0 | 62.03 |  |
| extract[durability#1] | low | 3284 | 461 | 3745 | 12037 | - | 0 | 61.82 |  |
| extract[durability#2] | low | 2154 | 108 | 2262 | 6221 | - | 0 | 61.41 |  |
| extract[materials#0] | low | 3189 | 281 | 3470 | 11930 | - | 0 | 61.82 |  |
| extract[materials#1] | low | 3540 | 632 | 4172 | 11888 | - | 0 | 62.35 |  |
| extract[materials#2] | low | 1783 | 142 | 1925 | 4848 | - | 0 | 61.59 |  |
| extract[materials#3] | low | 2000 | 130 | 2130 | 11357 | - | 0 | 1.2 |  |
| extract[materials#4] | low | 2834 | 117 | 2951 | 9224 | - | 0 | 59.77 |  |
| extract[production#0] | low | 3574 | 488 | 4062 | 12214 | - | 0 | 63.35 |  |
| extract[production#1] | low | 3459 | 373 | 3832 | 12254 | - | 0 | 62.35 |  |
| extract[cover_sampling#0] | low | 2830 | 162 | 2992 | 9121 | - | 0 | 64.93 |  |

Wall s per call includes the pacing sleep before the call (TPM budget 7,000/min).

## 3. Localization and routing (v2)

**run1**: Stage A picked 39 sections; safety nets added 4 (S046:descendant_of:S045, S047:descendant_of:S045, S050:descendant_of:S049, S054:descendant_of:S049). 127 units -> 113 routed to >=1 group, 14 to none. Retried ids: 0, defaulted to all groups: 0.

| Group | Units | Text chars | Text tokens (EST) | Extraction calls | Prompt tokens (MEASURED) |
|---|---:|---:|---:|---:|---:|
| grade_strength | 16 | 6,820 | 1,698 | 1 | 2,661 |
| durability | 40 | 32,012 | 7,989 | 3 | 9,600 |
| materials | 49 | 46,879 | 11,701 | 5 | 13,570 |
| production | 40 | 22,351 | 5,573 | 3 | 8,052 |
| cover_sampling | 18 | 10,533 | 2,628 | 1 | 3,504 |

**run2**: Stage A picked 38 sections; safety nets added 4 (S046:descendant_of:S045, S047:descendant_of:S045, S050:descendant_of:S049, S054:descendant_of:S049). 126 units -> 103 routed to >=1 group, 23 to none. Retried ids: 0, defaulted to all groups: 0.

| Group | Units | Text chars | Text tokens (EST) | Extraction calls | Prompt tokens (MEASURED) |
|---|---:|---:|---:|---:|---:|
| grade_strength | 13 | 5,721 | 1,425 | 1 | 2,370 |
| durability | 33 | 26,323 | 6,568 | 3 | 8,631 |
| materials | 45 | 44,588 | 11,131 | 5 | 13,346 |
| production | 37 | 20,865 | 5,203 | 2 | 7,033 |
| cover_sampling | 13 | 7,872 | 1,964 | 1 | 2,830 |

## 4. Per-parameter results

| Parameter | Group | v1 value | v1 audit | run1 value | run2 value | v2 run2 source quote | quote in doc? | v2 run2 audit |
|---|---|---|---|---|---|---|---|---|
| `specified_grade` | grade_strength | null | MISSING | null | null |  | - | MISSING |
| `specified_characteristic_strength` | grade_strength | null | MISSING | null | null |  | - | MISSING |
| `specified_sigma` | grade_strength | null | MISSING | null | null |  | - | MISSING |
| `specified_min_cement` | durability | 290 | FAIL | 290 | 290 | Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and co... | NO | FAIL |
| `specified_max_cement` | durability | null | MISSING | null | null |  | - | MISSING |
| `specified_wc` | durability | 0.55 | FAIL | 0.55 | 0.55 | Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and co... | NO | FAIL |
| `freezing_thawing_exposure` | durability | null | MISSING | null | null |  | - | MISSING |
| `measured_chloride_content` | durability | null | MISSING | null | null |  | - | MISSING |
| `measured_so3_percent` | durability | null | MISSING | null | null |  | - | MISSING |
| `cement_type` | materials | OPC | PASS | OPC | OPC | Ordinary Portland cement or Portland slag cement or Portland Pozzolana cement Super sulphated cement | yes | PASS |
| `water_ph` | materials | null | MISSING | 6.0 | 6.0 | The PH value of water shall not be less than 6 and more than 9. | yes | PASS |
| `water_organic_mg_l` | materials | 200.0 | PASS | 200.0 | 200.0 | Organic \| 200 mg/l | yes | PASS |
| `water_inorganic_mg_l` | materials | 3000.0 | PASS | 3000.0 | 3000.0 | Inorganic \| 3000 mg/l | yes | PASS |
| `water_sulphates_mg_l` | materials | 500.0 | FAIL | 500.0 | 500.0 | Sulphates (as SO4) \| 500 mg/l | yes | FAIL |
| `water_chlorides_mg_l` | materials | 1000.0 | FAIL | 1000.0 | 1000.0 | Chlorides (as C1)  \| 2000 mg/l for plain concrete work and 1000 mg/l for reinforced concrete work | yes | FAIL |
| `water_suspended_matter_mg_l` | materials | 2000.0 | PASS | 2000.0 | 2000.0 | Suspended matter   \| 2000 mg/l | yes | PASS |
| `mixing_time_minutes` | production | 2 | PASS | 2 | 2 | The mixer shall be run for a minimum period of 2 minutes after all materials are loaded in full quantity. | yes | PASS |
| `transport_time_minutes` | production | null | MISSING | 30 | 30 | Concrete shall be placed in position within 30 minutes from the time it is produced. | yes | PASS |
| `compaction_method` | production | mechanical vibrator | PASS | mechanical vibrator | mechanical vibrator | Concrete shall be thoroughly compacted, as depositing shall proceed by means of suitable vibrators. | yes | PASS |
| `specified_slump_mm` | production | null | MISSING | 35 | 35 | The slump shall be 25 mm to 35 mm depending upon the location and type of Work. | yes | PASS |
| `curing_days` | production | 7 | PASS | 7 | 7 | Starting 24 hours after placement of the concrete, the surface shall be cured by flooding with water or covering with damp Hessian cloth for a peri... | yes | PASS |
| `fire_resistance_rating` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `sampling_cube_size_mm` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `specified_sampling_sets` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `total_volume_m3` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `member_covers.Beams` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `member_covers.Columns` | cover_sampling | null | MISSING | null | null |  | - | MISSING |
| `member_covers.Slabs` | cover_sampling | null | MISSING | null | null |  | - | MISSING |

Not extracted by design: formwork (5 audit rows, always MISSING), and exposure / concrete_type / site SO3, which are supplied from outside (the 3 site-SO3 audit rows stay MISSING).

**Conflicts between batches (run1)** - first value in document order used, all kept:

- `specified_wc`: 0.55 (batch 0); 0.52 (batch 2)

**Conflicts between batches (run2)** - first value in document order used, all kept:

- `specified_wc`: 0.55 (batch 0); 0.52 (batch 1)

Cross-references (v2 run2):

- cement_type -> IS 8112: "43 Grade ordinary Portland cement conforming to IS 8112"
- water_testing -> IS 3025: "Water shall be tested in accordance with IS 3025."
- coarse_aggregate_grading -> IS 383: "Grading of coarse aggregate shall conform to the requirements in IS 383. See Table - 9."
- fine_aggregate_grading -> IS 383: "Grading of fine aggregate shall conform to IS 383 and shall fall within limits of one of the four zones given in table 4 of IS 383. See T..."
- mix_design -> IS 456, SP 23, SP 24: "The design shall be carried out strictly to IS specifications and IS code practice 456, SP 23 and SP 24."
- cube_testing_procedure -> IS 516: "Cubes shall be cast, stored, cured, transported and tested per IS 516."

Quote check (v2 run2): 18 found, 2 not found
- NOT FOUND `specified_min_cement`: "Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and co..."
- NOT FOUND `specified_wc`: "Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and co..."

## 5. MISSING parameters (v2 run2) - is the value in clean.md?

22 MISSING audit rows. 8 are by design: 5 formwork rows (skipped) and 3 site soil/groundwater SO3 rows (supplied from outside; the BLR spec has no site values, and Table 6 only gives class thresholds). The other 14 rows (12 parameters) were searched in `clean.md` by hand. Routing was traced in `output_v2/run2/units.json` + `routing.json`, and extraction in `output_v2/run2/extract_calls/`.

| Parameter | In clean.md? | Where / wording | Unit -> routed to (run2) | Verdict |
|---|---|---|---|---|
| `measured_chloride_content` | **Yes, as a limit** | 2.7 A: "...or 0.6 kg/m 3 of concrete" (soluble chloride ion limit) | S026.U1 -> `materials` only (run1: `materials`+`durability`) | **Routing miss in run2** (the param is in `durability`). In run1 it was routed correctly but the durability call returned null, so it was an **extraction miss** there. |
| `sampling_cube_size_mm` | **Yes, indirectly** | Table 4 NOTE 1: "...15 cm cube at 28 days"; 2.6 C.1: "three 15 cm concrete cubes". The sampling clause only says "Each sample shall consist of 6 cubes" (no size) | S019.U2 -> `grade_strength`; S024.U2 -> `durability`,`materials` (same in run1) | **Routing miss** (never sent to `cover_sampling`). Borderline: the size is not stated in the sampling clause itself. |
| `member_covers` (Beams/Columns/Slabs, 3 rows) | By reference | 3.5 F.1: "...cover shall be as specified in the Drawings or as directed by the ER" | S048.U1 -> `cover_sampling` | **Stated only by reference (drawings)**. Routed correctly, correctly null. |
| `specified_grade` | No single value | 2.3: grades "as shown in Table 4" (a list M10-M60); NOTE 3: not lower than M 15 for RC | S019.U2 -> `grade_strength` | **By reference / list only**. Correctly null under the groups.py rule. |
| `specified_characteristic_strength` | No single value | Follows the grade; Table 4 maps every grade | S019 units -> `grade_strength` | **Not determinable** (no grade) |
| `specified_sampling_sets` | Rule only | 3.9 / 3.10 frequency tables (volume-dependent) | S060.U3 -> `cover_sampling`,`production` | **Rule, not a single value**. Needs `total_volume_m3`. |
| `total_volume_m3` | No | No project quantity in the spec | - | **Truly absent** |
| `specified_sigma` | No | "standard deviation" not in doc | - | **Truly absent** |
| `specified_max_cement` | No | No maximum cement content clause | - | **Truly absent** |
| `fire_resistance_rating` | No | "fire" only in reference-list titles (IS 1641-1643, IS 3809) | S003 units (reference list) -> tagged, nothing to extract | **Truly absent** |
| `freezing_thawing_exposure` | No | "freezing" only inside Table 5 exposure-class descriptions | S021.U1 -> `durability` | **Truly absent** (correctly null under the groups.py rule) |
| `measured_so3_percent` | No | No SO3 limit for concrete/cement | - | **Truly absent** |

**Summary (14 non-design MISSING rows):**
- 2 routing misses: chloride limit (run2 only) and cube size (both runs).
- 0 extraction misses in run2. Run1 had one: the chloride limit.
- 5 rows stated only by reference or as a rule: covers x3, grade, sampling sets.
- 7 truly absent: characteristic strength (follows grade), volume, sigma, max cement, fire rating, freezing, SO3.

**v1's 5 extraction misses, in v2:** transport time (30 min), slump (35 mm) and water pH (6.0) are now found in both runs. The chloride limit and cube size are still missed, now at routing instead of extraction.

**Wrong or questionable values (not MISSING):**
- `specified_wc` = 0.55: a conflict in both runs. The durability batch with Table 5 gave 0.55; the batch with mix-design clause 3.6 B.d ("between 0.5 to 0.52") gave 0.52. The merge keeps the first value in document order and records the conflict. The groups.py rule "mix-design clause takes priority" cannot work across batches. Both values FAIL against IS 456 Moderate/RC max 0.50, so the audit status is unaffected here.
- `curing_days` = 7: 3.6 P says 7 days of flooding / damp Hessian, then "For the next 7 days the surface shall be kept wet". The groups.py "add consecutive periods" rule (14) was not followed. Both values PASS (min 7).
- run2 quotes for `specified_min_cement` and `specified_wc` are composed, not verbatim (row label + column header + cell). The values match the Table 5 Moderate / RC cells (290, 0.55). The deterministic check correctly flags them.
- run2 `cement_type` = OPC is right (2.5 A), but its quote is a Table 6 sulphate-class row that lists several cement types: weak support.

## 6. Consistency: run1 vs run2

**Caveat:** run2 is not an identical re-run. Between the runs the extraction prompt's CROSS-REFERENCES paragraph was restored to parser.py's wording (run1 returned 0 cross-references; see CHANGES.md). Stage A, units and routing code are identical, so scope/routing differences are pure LLM nondeterminism; extracted-value differences may partly come from the prompt change.

- In-scope sections: run1 43, run2 42; only in run1: ['S000', 'S001']; only in run2: ['S036'].
- Units: run1 127, run2 126; common 126; common units with different group tags: 35 (28%).
- Extracted values that differ: 0
- Audit statuses that differ: 6
  - `Cement Type (Cross-Reference)`: None vs PASS
  - `Coarse Aggregate Grading (Cross-Reference)`: None vs PASS
  - `Cube Testing Procedure (Cross-Reference)`: None vs PASS
  - `Fine Aggregate Grading (Cross-Reference)`: None vs PASS
  - `Mix Design (Cross-Reference)`: None vs PASS
  - `Water Testing (Cross-Reference)`: None vs PASS
- Audit counts: run1 {'PASS': 13, 'MISSING': 22, 'FAIL': 4} vs run2 {'PASS': 19, 'MISSING': 22, 'FAIL': 4}.
- Total tokens (MEASURED): run1 64,878 vs run2 61,954.


## 7. v2 after the JSON structure change (shapes)

Added after report_v2.py generated sections 1-6 (re-running report_v2.py rewrites the file without this section; the numbers below come from experiments/shapes/token_table.py). run3 and run4 are BLR runs of the same v2 pipeline after the parameter-shapes change. What differs from v2 run1/run2:

- one more extraction group (aggregates: IS 383 deleterious limits and grading tables);
- longer extraction prompt (two-line table quotes, references incl. drawings, remarks, ranges);
- Docling table padding squeezed before sending (e.g. one table 9.1k -> 2.5k chars);
- table-valued fields merged cell by cell across batches.

run3 and run4 differ only by LLM nondeterminism (Stage A picked a different set of sections, so routing and the number of extraction batches differ). An NMP Noida run (nmp1) failed at section picking (Groq json_validate_failed, empty output, 3 tries) and is not included.

MEASURED (Groq API usage field):

| Metric | v1 | v2 run1 | v2 run2 | v2-shapes run3 | v2-shapes run4 |
|---|---:|---:|---:|---:|---:|
| API calls | 12 | 19 | 18 | 13 | 20 |
| Input (prompt) tokens | 31,552 | 54,827 | 51,554 | 41,868 | 62,722 |
| Output (completion) tokens, incl. hidden reasoning | 10,683 | 10,051 | 10,400 | 12,671 | 14,312 |
| **Total tokens** | **42,235** | **64,878** | **61,954** | **54,539** | **77,034** |
| Largest single call (total) | 5132 | 5003 | 4771 | 5937 | 5108 |
| 429 retries | 0 | 0 | 0 | 0 | 0 |
| Call errors | 0 | 0 | 0 | 0 | 0 |

**Per step: input / output tokens**

| Step | v1 | v2 run1 | v2 run2 | v2-shapes run3 | v2-shapes run4 |
|---|---:|---:|---:|---:|---:|
| 1 section picking | 2,171 / 2,961 (1) | 2,171 / 2,832 (1) | 2,171 / 2,600 (1) | 2,171 / 2,297 (1) | 2,171 / 2,937 (1) |
| 2 routing | - | 15,269 / 4,466 (5) | 15,173 / 4,386 (5) | 12,514 / 3,625 (4) | 15,668 / 4,779 (5) |
| 3 extract (v1 group): cover_sampling | 5,562 / 1,096 (2) | - | - | - | - |
| 3 extract (v1 group): durability_grade | 2,544 / 758 (1) | - | - | - | - |
| 3 extract (v1 group): materials | 10,306 / 2,839 (4) | - | - | - | - |
| 3 extract (v1 group): production_curing | 10,969 / 3,029 (4) | - | - | - | - |
| 3 extract: aggregates | - | - | - | 6,965 / 3,740 (2) | 10,193 / 2,523 (3) |
| 3 extract: cover_sampling | - | 3,504 / 180 (1) | 2,830 / 162 (1) | 2,801 / 827 (1) | 5,409 / 1,510 (2) |
| 3 extract: durability | - | 9,600 / 751 (3) | 8,631 / 998 (3) | 3,800 / 673 (1) | 10,180 / 943 (3) |
| 3 extract: grade_strength | - | 2,661 / 119 (1) | 2,370 / 91 (1) | 3,184 / 113 (1) | 3,127 / 104 (1) |
| 3 extract: materials | - | 13,570 / 975 (5) | 13,346 / 1,302 (5) | 3,632 / 523 (1) | 6,822 / 701 (2) |
| 3 extract: production | - | 8,052 / 728 (3) | 7,033 / 861 (2) | 6,801 / 873 (2) | 9,152 / 815 (3) |

Cell format: input / output (number of calls). Output includes the model's hidden reasoning; Groq's usage field as logged does not split it out.
