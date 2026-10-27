# run2 vs run4 (BLR)

Audit recomputed with the current auditor for both runs. Stored counts: run2 {'pass': 19, 'fail': 4, 'warning': 22, 'total': 45}, run4 {'pass': 20, 'fail': 5, 'warning': 19, 'reference': 6, 'total': 44}.

Current-auditor counts: run2 {'pass': 18, 'fail': 4, 'warning': 25, 'reference': 5, 'total': 47} (38% passed, of which 5 are references); run4 {'pass': 20, 'fail': 5, 'warning': 19, 'reference': 6, 'total': 44} (45% passed, of which 6 are references).

Tokens (MEASURED): run2 61,954 in 18 calls; run4 77,034 in 20 calls.

| field | run2 value | run4 value | run4 quote in doc? | run2 status | run4 status | run4 remark |
|---|---|---|---|---|---|---|
| `concrete_type` | Reinforced Concrete | Reinforced Concrete | - | PASS | PASS |  |
| `exposure` | Moderate | Moderate | - | PASS | PASS |  |
| `cement_type` | OPC | OPC | yes | PASS | PASS |  |
| `soil_total_so3_percent` | null | null | - | MISSING | MISSING |  |
| `soil_extract_2_1_so3_gl` | null | null | - | MISSING | MISSING |  |
| `groundwater_so3_gl` | null | null | - | MISSING | MISSING |  |
| `freezing_thawing_exposure` | null | null | - | MISSING | MISSING |  |
| `specified_grade` | null | null | - | MISSING | MISSING |  |
| `specified_min_cement` | 290 | 290 | yes | FAIL | FAIL |  |
| `specified_max_cement` | null | null | - | MISSING | MISSING |  |
| `specified_wc` | 0.55 | 0.55 | yes | FAIL | FAIL | The document states different values (0.55, [0.5, 0.52]); the first in document order i... |
| `specified_sigma` | null | null | - | MISSING | MISSING |  |
| `specified_characteristic_strength` | null | null | - | MISSING | MISSING |  |
| `fire_resistance_rating` | null | null | - | MISSING | MISSING |  |
| `mixing_time_minutes` | 2 | 2 | yes | PASS | PASS |  |
| `transport_time_minutes` | 30 | 30 | yes | PASS | PASS |  |
| `compaction_method` | mechanical vibrator | mechanical vibrator | yes | PASS | PASS |  |
| `curing_days` | 7 | 14 | yes | PASS | PASS |  |
| `specified_slump_mm` | 35 | [25, 35] | yes | PASS | PASS |  |
| `water_ph` | 6.0 | [6, 9] | yes | PASS | PASS |  |
| `water_organic_mg_l` | 200.0 | 200 | yes | PASS | PASS |  |
| `water_inorganic_mg_l` | 3000.0 | 3000 | yes | PASS | PASS |  |
| `water_sulphates_mg_l` | 500.0 | 500 | yes | FAIL | FAIL |  |
| `water_chlorides_mg_l` | 1000.0 | 1000 | yes | FAIL | FAIL |  |
| `water_suspended_matter_mg_l` | 2000.0 | 2000 | yes | PASS | PASS |  |
| `measured_chloride_content` | null | null | - | MISSING | MISSING |  |
| `measured_so3_percent` | null | null | - | MISSING | MISSING |  |
| `aggregate_deleterious_limits` | null | {"fine uncrushed": {"coal and lignite": 1.... | yes | MISSING | FAIL |  |
| `coarse_aggregate_grading` | null | null | - | REFERENCE | REFERENCE |  |
| `fine_aggregate_grading` | null | null | - | REFERENCE | REFERENCE |  |
| `all_in_aggregate_grading` | null | null | - | MISSING | REFERENCE |  |
| `total_volume_m3` | null | null | - | MISSING | MISSING |  |
| `sampling_cube_size_mm` | null | null | - | MISSING | MISSING |  |
| `specified_sampling_sets` | null | null | - | MISSING | MISSING |  |
| `sampling_frequency` | null | [{"from_m3": 0, "to_m3": 5, "samples": 2, ... | yes | MISSING | PASS | The document states different values ([{"from_m3": 0, "to_m3": 5, "samples": 2, "extra_... |
| `member_covers.Beams` | null | null | - | MISSING | REFERENCE |  |
| `member_covers.Columns` | null | null | - | MISSING | REFERENCE |  |
| `member_covers.Slabs` | null | null | - | MISSING | REFERENCE |  |

**References (run4)**

- member_covers -> drawings: "Reinforcement shall have concrete cover and the thickness of such cover shall be as specified in the Drawings or as d..."
- coarse_aggregate_grading -> IS 383: "Grading of coarse aggregate shall conform to the requirements in IS 383. See Table - 9."
- fine_aggregate_grading -> IS 383: "Grading of fine aggregate shall conform to IS 383 and shall fall within limits of one of the four zones given in tabl..."
- all_in_aggregate_grading -> IS 383: "All-In Aggregate Grading: See Table 11 for all-in aggregate grading for nominal sizes 40 and 20."

**Quote check (run4)**: 20 found, 0 not found

Table quotes: 9 of 9 pass; number not in quoted row: none

**Non-pass rows (run4, current auditor)**

- MISSING Soil Total SO3: Not Provided | Limit depends on class
- MISSING Soil Extract SO3: Not Provided | Limit depends on class
- MISSING Groundwater SO3: Not Provided | Limit depends on class
- MISSING Freezing and Thawing: Not Provided | Defined
- MISSING Concrete Grade: Not Provided | Min M25
- FAIL Min Cement Content: 290 kg/m³ | Min 300 kg/m³
- MISSING Max Cement Content: Not Provided | Max 450 kg/m³
- FAIL W/C Ratio: 0.55 | Max 0.5
- MISSING Standard Deviation (sigma): Not Provided | Based on Grade
- MISSING Characteristic Strength: Not Provided | Expected value
- MISSING Fire Resistance Rating: Not Provided | Required for cover
- FAIL Water - Sulphates: 500 mg/l | Max 400 mg/l
- FAIL Water - Chlorides: 1000 mg/l | Max 500 mg/l
- MISSING Chloride Content: Not Provided | Max 0.6 kg/m³
- MISSING Sulphate (SO3) Content: Not Provided | Max 4 %
- FAIL Aggregate - Deleterious Materials: 18 values in 4 group(s) | Within IS 383:2016 Table 2; outside: coarse uncrushed finer than 75 um: 3 > 1; coarse crushed finer than 75 um: 3 > 1; coarse crushed total: 5 > 2
- MISSING Total Volume: Not Provided | Required for sampling
- MISSING Cube Size: Not Provided | 150 mm
- MISSING Sampling Sets: Not Provided | Volume and Sets Required
- MISSING Formwork Removal - Walls/Columns: Not Provided | Min 16 hrs
- MISSING Formwork Removal - Slabs (props left under): Not Provided | Min 3 days
- MISSING Formwork Removal - Beam Soffit (props left under): Not Provided | Min 7 days
- MISSING Formwork Removal - Props Under Slabs: Not Provided | Depends on span
- MISSING Formwork Removal - Props Under Beams/Arches: Not Provided | Depends on span
