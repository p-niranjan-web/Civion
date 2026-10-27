# Fallback keyword search — evaluation on BLR

## What I ran vs. what I judged

**Ran (scripts, reproducible):**
- `search.py` on `experiments/parse_test/docling_output.md` (the only document opened) with `keywords_v0.json`, the round-1 list (`runs/keywords_r1.json`) and the final `keywords.json`. Each run's hits are in `runs/hits_*.json`.
- `runs/evaluate.py` compares every hit with `labels.json` and computes the counts below. It asserts that no hit is unlabelled.
- The document splits into 783 units (sentences, list items, table rows and headers). Python stdlib only. No LLM calls.

**Judged by reading (my labels, not computed):**
- Every hit's RELEVANT/IRRELEVANT label in `labels.json`. 155 distinct (parameter, unit) labels.
- The reason each parameter has no relevant hit, and the list of relevant passages the final search still misses. I got both by reading all 1271 lines of the BLR document once, after keywords_v0.json was saved.
- So recall is my judgement from that read-through. It is not a computed number, and a second reader could disagree on borderline labels (listed at the end).

**Order kept:** keywords_v0.json was written from parser.py, database.py and general IS/ACI/BS wording before BLR was opened. Held-out folders (`sample_spec_docs/`, `docling_samples/`) were not opened. No existing file was modified.

## Summary

| run | hits | relevant | precision | params with ≥1 relevant |
|---|---|---|---|---|
| v0 (keywords_v0 + search.py as first written) | 107 | 57 | 0.53 | 17 / 25 |
| keywords_v0 + final search.py (to separate code changes from keyword changes) | 103 | 57 | 0.55 | 17 / 25 |
| round 1 | 135 | 76 | 0.56 | 20 / 25 |
| **final (keywords.json + final search.py)** | **109** | **76** | **0.70** | **20 / 25** |

The code changes on their own (row 2) changed little. Recall gains needed both: the code changes (multi-row headers, page-break re-joining) and the keyword fixes (superscript units, cross-reference hint, cm cube sizes).

## Per parameter

"Hits / relevant." Final irrelevant = final hits − final relevant.

| Parameter | v0 hits / relevant | final hits / relevant | final irrelevant | ≥1 relevant (v0 → final) |
|---|---|---|---|---|
| `water_ph` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `specified_grade` | 10 / 1 | 14 / 3 | 11 | yes → yes |
| `cement_type` | 17 / 12 | 16 / 13 | 3 | yes → yes |
| `specified_min_cement` | 0 / 0 | 8 / 7 | 1 | **no** → yes |
| `specified_max_cement` | 0 / 0 | 0 / 0 | 0 | **no** → **no** |
| `specified_wc` | 7 / 7 | 7 / 7 | 0 | yes → yes |
| `specified_characteristic_strength` | 12 / 8 | 13 / 10 | 3 | yes → yes |
| `specified_sigma` | 0 / 0 | 0 / 0 | 0 | **no** → **no** |
| `mixing_time_minutes` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `transport_time_minutes` | 1 / 1 | 2 / 2 | 0 | yes → yes |
| `compaction_method` | 22 / 5 | 14 / 5 | 9 | yes → yes |
| `curing_days` | 6 / 3 | 3 / 3 | 0 | yes → yes |
| `specified_slump_mm` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `total_volume_m3` | 9 / 0 | 0 / 0 | 0 | **no** → **no** |
| `specified_sampling_sets` | 11 / 11 | 14 / 13 | 1 | yes → yes |
| `sampling_cube_size_mm` | 1 / 0 | 5 / 2 | 3 | **no** → yes |
| `measured_chloride_content` | 1 / 0 | 2 / 1 | 1 | **no** → yes |
| `measured_so3_percent` | 0 / 0 | 0 / 0 | 0 | **no** → **no** |
| `fire_resistance_rating` | 0 / 0 | 0 / 0 | 0 | **no** → **no** |
| `member_covers` | 2 / 1 | 3 / 2 | 1 | yes → yes |
| `water_organic_mg_l` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `water_inorganic_mg_l` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `water_sulphates_mg_l` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `water_chlorides_mg_l` | 1 / 1 | 1 / 1 | 0 | yes → yes |
| `water_suspended_matter_mg_l` | 1 / 1 | 1 / 1 | 0 | yes → yes |

## Parameters with no relevant hit (final)

| Parameter | Reason (judged by reading BLR) |
|---|---|
| `specified_max_cement` | **Truly absent.** BLR gives no maximum cement content (IS 456 8.2.4.2 says 450 kg/m³). The only "maximum … kg/m³" is a fly-ash cap ("maximum of (220kg/m 3)" in the fly-ash clause), which is not a cement-content limit. The round-2 qualifier rule (D3) dropped 9 false hits from the minimum-cement tables. |
| `specified_sigma` | **Truly absent.** BLR has no standard deviation and no target mean strength. The closest text is "statistical procedures for required average strength shall be utilized", which has no value and does not name σ. |
| `total_volume_m3` | **Truly absent.** BLR never states a project quantity. Every m³ figure is a band in the sampling-frequency table, and those are now excluded (C8). |
| `measured_so3_percent` | **Truly absent for concrete.** The only SO₃ percentages are soil SO₃ classes in the sulphate-attack table (a user-supplied field). Admixture clauses say "indicate chloride and sulphate content" and "do not use admixtures which contain … sulphates", with no limit. |
| `fire_resistance_rating` | **Truly absent.** It appears only as code titles in the reference list (IS 1641/1642/1643, IS 3809 "Fire Resistance Test…"), which the reference-line exclude removes as intended. No rating or "as per drawings" statement. |

## Relevant passages the final search still misses (judged by reading)

- **All five water_* fields:** "Maximum permissible limits of deleterious materials in water shall be as given in IS 456 and Table --7." This is a cross-reference, but it names none of the five solids, so no per-parameter term can match it. The table rows themselves are found, so nothing is lost here. On a spec that has only this sentence and no table, the five parameters would be missed.
- **`specified_sampling_sets`:** "Three cubes shall be tested on the 7 th day and other three cubes on the 28 th day." This gives the sample composition. It has no sampling term ("sample", "sets").
- **`member_covers`:** "…nearer than the specified cover to the finished surface…" has no value and no deferral, so missing it is acceptable.
- **`sampling_cube_size_mm`:** the cylinder clauses ("Cure the cylinders…", "25 standard cylinder molds") give no size, so missing them is acceptable.
- **`specified_grade`:** the project's actual grade is not stated in BLR (presumably on the drawings, but BLR does not say so). The relevant hits are the minimum-grade rule (M15 for RC) and the deferrals to Table 4 / IS 456 Table 2.

## Remaining false-hit patterns (not fixed, no general fix found)

- `specified_grade` (11 irrelevant): the grade/fck table rows (`M 10 | 10` …) list all designations, not the specified grade. Excluding them would also drop them for `specified_characteristic_strength`, where they are relevant.
- `compaction_method` (9 irrelevant): formwork-design clauses ("withstand mechanical vibrators", "placing, ramming, vibration"), bar spacing for needle vibrators, the "Formwork for Vibrated Concrete" sub-heading (a list item, so D9 can't see it), and a list of site operations. Descriptive parameters with no value filter are inherently noisy. A downstream LLM has to decide.
- `sampling_cube_size_mm` (3), `specified_characteristic_strength` (3), `measured_chloride_content` (1: grout "free of … chlorides" plus an unrelated "95%"), `member_covers` (1: "(1.6mm) wire" near "spacers"), `specified_min_cement` (1: the `Kg/m 3 | Kg/m 3` unit row), `specified_sampling_sets` (1: welding-sample frequency "as directed").

## Labelling judgement calls (a second reader may differ)

- Grade/fck table rows: **irrelevant** for `specified_grade` (they list designations, not the specified grade) but **relevant** for `specified_characteristic_strength`. The clause above the table says the fck values "in the Work shall be as shown in Table 4".
- "fly ash content of above 30%" (LEED goal): **relevant** to `cement_type` (it signals a mineral-admixture binder).
- "15 cm cube" in the grade-designation note and in the water-suitability test: **relevant** to `sampling_cube_size_mm`.
- "Contractor shall provide … mixers, vibrators": **relevant** to `compaction_method`.
- Rows of the sulphate-attack table: **relevant** to `cement_type`, `specified_min_cement` and `specified_wc` (they state requirements by sulphate class). Its header row is irrelevant.

## Example hits (final run; up to 3 per parameter, relevant first, [R]/[I] = my label)

**`water_ph`**
- L571 [R] 3. The PH value of water shall not be less than 6 and more than 9.

**`specified_grade`**
- L479 [R] - A. Concrete Grade Designations and corresponding required characteristic compressive strength in the Work shall be as shown in Table 4.
- L507 [R] - NOTE - 3 Grades of concrete lower than M 15 shall not be used in reinforced concrete.
- L986 [R] - a. Concrete shall be classified by its compressive strength at the 28th day. The concrete grades shall be as designated in table 2 of IS 456 and are given as ready reference in Table - 4.

**`cement_type`**
- L245 [R] - b. Recycled Content: Concrete products shall strive to achieve a fly ash content of above 30%, but shall not exceed the requirements of IS 1489 (Part 1).
- L541 [R] 1) \| Less than 0.2 \| -- \| Less than 30 \| Ordinary Portland cement or Portland slag cement or Portland Pozzolana cement \| 280 kg/m 3 \| 0.55
- L542 [R] 2) \| 0.2 to 0.5 \| -- \| 30 to 120 \| Ordinary Portland cement or Portland slag cement or Portland Pozzolana cement Super sulphated cement \| 330 kg/m 3 310 kg/m 3 \| 0.50 0.50

**`specified_min_cement`**
- L523 [R] Mild - for example, completely protected against weather, or aggressive conditions, except for a brief period of exposure to normal weather conditions during construction. \| 220 \| 0.7 \...
- L524 [R] Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and concrete continuously under water. \| 250 ...
- L525 [R] Severe - For example, exposed to sea water, alternate wetting and drying and to freezing whilst wet, subject to heavy condensation or corrosive fumes. \| 310 \| 0.5 \| 360 \| 0.45

**`specified_max_cement`**
- (no hits)

**`specified_wc`**
- L523 [R] Mild - for example, completely protected against weather, or aggressive conditions, except for a brief period of exposure to normal weather conditions during construction. \| 220 \| 0.7 \...
- L524 [R] Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in soil and concrete continuously under water. \| 250 ...
- L525 [R] Severe - For example, exposed to sea water, alternate wetting and drying and to freezing whilst wet, subject to heavy condensation or corrosive fumes. \| 310 \| 0.5 \| 360 \| 0.45

**`specified_characteristic_strength`**
- L479 [R] - A. Concrete Grade Designations and corresponding required characteristic compressive strength in the Work shall be as shown in Table 4.
- L490 [R] M 10 \| 10
- L491 [R] M 15 \| 15

**`specified_sigma`**
- (no hits)

**`mixing_time_minutes`**
- L1024 [R] 4. The mixer shall be run for a minimum period of 2 minutes after all materials are loaded in full quantity. The concrete produced shall be uniform in colour and consistency.

**`transport_time_minutes`**
- L361 [R] 3. When the temperature is above (32 deg. C.), reduce the mixing/delivery time from 11/2 hrs. to 1-1/4 hrs. Cool forms to a maximum of (27 deg. C.) Cool concrete to maximum of (21 deg. C....
- L1063 [R] 6. All slabs, beams, wooden planks and cat-walks shall be provided clear of reinforcement. Concrete shall be placed in position within 30 minutes from the time it is produced. Concrete sh...

**`compaction_method`**
- L906 [R] 1. If external vibrators are to be used for compacting the concrete, appropriate type of vibrator, design of the formwork and the method of fixing the vibrators shall be used.
- L1022 [R] 2. The Contractor shall provide concrete batch mixers, vibrators, weight batches conforming to relevant IS specification. The capacity and number of mixers and vibrators required at site ...
- L1068 [R] 1. Concrete shall be thoroughly compacted, as depositing shall proceed by means of suitable vibrators. The vibrators shall maintain the entire concrete under treatment in an adequate stat...

**`curing_days`**
- L1114 [R] 1. After concrete has begun to harden i.e. about 1 to 2 hours after placement, it shall be protected from quick drying with moist or damped Hessian cloth or any other material approved by...
- L1115 [R] 2. For the next 7 days the surface shall be kept wet all the time by sprinkling water continuously.
- L1116 [R] 3. For Mass Concrete: Curing period shall be 14 days.

**`specified_slump_mm`**
- L995 [R] - d. For expected strength of cubes tested on the 28 th day the design mix at preliminary test and work site shall be as per IS 456, SP 23 and SP 24. The water cement ratio shall be betwe...

**`total_volume_m3`**
- (no hits)

**`specified_sampling_sets`**
- L1178 [R] 5. The minimum frequency of cube casting for testing shall be as follows. Each sample shall consist of 6 cubes.
- L1188 [R] Up to 5 cu.m. in a day \| 15 cu.m. to 15 cu.m. \| 2
- L1189 [R] 15 cu.m. to 30 cu.m. \| 3

**`sampling_cube_size_mm`**
- L505 [R] - NOTE - 1 In the designation of a concrete of mix, letter M refers to the mix and the number to the specified characteristic compressive strength of 15 cm cube at 28 days, expressed in N...
- L569 [R] 1. Average 28 days compressive strength of at least three 15 cm concrete cubes prepared with water proposed to be used shall not be less than 90% of the average strength of three similar ...
- L995 [I] - d. For expected strength of cubes tested on the 28 th day the design mix at preliminary test and work site shall be as per IS 456, SP 23 and SP 24. The water cement ratio shall be betwe...

**`measured_chloride_content`**
- L591 [R] - A. General: Admixtures shall conform to the requirements of IS 9103, ASTM C260, ASTM C10, ASTM C 595 or ASTM C 618. Use shall conform to the requirements of IS 456 and IS 9103. Calcium ...
- L750 [I] - D. Grout: Free of gas-producing or gas-releasing agents, oxidizing catalysts, inorganic accelerators and chlorides. If requested by the ER, grout a sample (1.2m) x(1.2m) x (50mm) plate ...

**`measured_so3_percent`**
- (no hits)

**`fire_resistance_rating`**
- (no hits)

**`member_covers`**
- L954 [R] 1. Reinforcement shall have concrete cover and the thickness of such cover shall be as specified in the Drawings or as directed by the ER.
- L959 [R] 2. But in no case shall the cover be reduced by more than 5 mm of that specified. There shall be no compromise on cover for foundation work.
- L923 [I] - B. Position, support, and secure reinforcement against displacement by formwork, construction, or concrete placement operations. Locate and support reinforcing with metal chairs, runner...

**`water_organic_mg_l`**
- L581 [R] Organic \| 200 mg/l

**`water_inorganic_mg_l`**
- L582 [R] Inorganic \| 3000 mg/l

**`water_sulphates_mg_l`**
- L583 [R] Sulphates (as SO4) \| 500 mg/l

**`water_chlorides_mg_l`**
- L584 [R] Chlorides (as C1) \| 2000 mg/l for plain concrete work and 1000 mg/l for reinforced concrete work

**`water_suspended_matter_mg_l`**
- L585 [R] Suspended matter \| 2000 mg/l
