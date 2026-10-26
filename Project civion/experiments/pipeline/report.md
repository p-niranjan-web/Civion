# Civion localization + extraction pipeline - BLR run report

Args: exposure=`Moderate`, concrete_type=`Reinforced Concrete`, max tokens/call (target)=`5000`. Model: `openai/gpt-oss-120b`.

Legend: **MEASURED** = counted by code or taken from the Groq API `usage` field. **EST** = estimate (chars / 4).

## 1. Document size: whole doc vs localized

| Text | Chars (MEASURED) | Tokens (EST, chars/4) | % of clean.md |
|---|---:|---:|---:|
| docling_output.md (raw) | 137,801 | 34,450 | 101.2% |
| clean.md (whole doc) | 136,124 | 34,031 | 100.0% |
| localized.md | 84,282 | 21,070 | 61.9% |

For comparison, today's parser.py sends `clean_text[:12000]` (~3,000 EST tokens) of its own pdfplumber text.

clean.py removed 102 `<!-- image -->` markers and 0 repeated header/footer lines (no normalized line < 120 chars repeats 3+ times in this doc once images are gone).

## 2. API calls (MEASURED usage) and wall time

| Call | reasoning_effort | Prompt tok | Completion tok | Total tok | Text sent (chars) | Retries (429) | Wall s | Error |
|---|---|---:|---:|---:|---:|---:|---:|---|
| localize | medium | 2171 | 2961 | 5132 | - | 0 | 7.46 |  |
| extract[0] materials | low | 2595 | 1041 | 3636 | 6275 | 0 | 63.2 |  |
| extract[1] materials | low | 3050 | 798 | 3848 | 9096 | 0 | 62.73 |  |
| extract[2] materials | low | 2022 | 491 | 2513 | 9219 | 0 | 62.43 |  |
| extract[3] materials | low | 2639 | 509 | 3148 | 7184 | 0 | 1.62 |  |
| extract[4] durability_grade | low | 2544 | 758 | 3302 | 8912 | 0 | 62.71 |  |
| extract[5] production_curing | low | 3265 | 463 | 3728 | 9104 | 0 | 62.13 |  |
| extract[6] production_curing | low | 1937 | 681 | 2618 | 3496 | 0 | 62.44 |  |
| extract[7] production_curing | low | 2861 | 1147 | 4008 | 7639 | 0 | 63.46 |  |
| extract[8] production_curing | low | 2906 | 738 | 3644 | 8224 | 0 | 62.62 |  |
| extract[9] cover_sampling | low | 2881 | 489 | 3370 | 8133 | 0 | 62.03 |  |
| extract[10] cover_sampling | low | 2681 | 607 | 3288 | 6707 | 0 | 62.12 |  |
| **Total** | | **31,552** | **10,683** | **42,235** | | | | |

Calls over the 5000-token target (MEASURED): localize (5132). Completion tokens include gpt-oss hidden reasoning tokens.

Wall time per step (MEASURED; extract includes the deliberate TPM pacing sleeps):

| Step | Wall s |
|---|---:|
| clean | 0.016 |
| sections | 0.048 |
| localize | 9.06 |
| extract | 627.88 |
| audit | 0.0 |
| **total** | **637.00** |

## 3. Localization

- Sections: 62 total, **36 selected**, 26 not selected (5 of all sections have no body text, e.g. PART headings).
- Tables: 17 total, 13 included in localized.md.
- Parents added by the deterministic 'picked child -> keep parent text' rule: ['S002', 'S045'].
- Unknown ids returned by the model: none.
- `production_curing`: S002, S003, S004, S005, S009, S034, S036, S037, S038, S039, S049, S051, S052, S053, S055
- `cover_sampling`: S008, S045, S048, S058, S059, S060
- `durability_grade`: S018, S019, S020, S021, S022
- `materials`: S023, S024, S025, S026, S027, S028, S029, S030, S031, S032

Selected headings:

```
S002 [production_curing] PART 1 - GENERAL > 1.2 REFERENCES
S003 [production_curing] PART 1 - GENERAL > 1.2 REFERENCES > SECTION 03 30 00 / CAST- IN-PLACE CONCRETE
S004 [production_curing] PART 1 - GENERAL > 1.3 SYSTEM DESCRIPTION
S005 [production_curing] PART 1 - GENERAL > 1.3 SYSTEM DESCRIPTION > A. Performance Requirements
S008 [cover_sampling] PART 1 - GENERAL > 1.5 QUALITY ASSURANCE
S009 [production_curing] PART 1 - GENERAL > 1.6 DELIVERY, STORAGE AND HANDLING
S018 [durability_grade] PART 2 - PRODUCTS > 2.3 GRADES OF CONCRETE
S019 [durability_grade] PART 2 - PRODUCTS > 2.3 GRADES OF CONCRETE > TABLE -- 4 / CONCRETE GRADES AND CHARACTERISTIC COMPRESSIVE STRENGTHS
S020 [durability_grade] PART 2 - PRODUCTS > 2.4 DURABILITY AND COMPATIBILITY REQUIREMENTS FOR CONCRETE AND MATERIALS
S021 [durability_grade] PART 2 - PRODUCTS > 2.4 DURABILITY AND COMPATIBILITY REQUIREMENTS FOR CONCRETE AND MATERIALS > TABLE - 5 / MINIMUM CEMENT CONTENT REQUIRED IN CEMENT CONCRETE TO ENSURE DURABILITY UNDER SPECIFIED CONDITIONS OF EXPOSURE
S022 [durability_grade] PART 2 - PRODUCTS > 2.4 DURABILITY AND COMPATIBILITY REQUIREMENTS FOR CONCRETE AND MATERIALS > TABLE - 6 / REQUIREMENTS FOR CONCRETE EXPOSED TO SULPHATE ATTACK
S023 [materials] PART 2 - PRODUCTS > 2.5 CEMENT MATERIALS
S024 [materials] PART 2 - PRODUCTS > 2.6 WATER
S025 [materials] PART 2 - PRODUCTS > 2.6 WATER > TABLE - 7 / PERMISSIBLE LIMITS FOR SOLIDS (IN WATER)
S026 [materials] PART 2 - PRODUCTS > 2.7 ADMIXTURES FOR CONCRETE
S027 [materials] PART 2 - PRODUCTS > 2.8 AGGREGATES FOR CONCRETE
S028 [materials] PART 2 - PRODUCTS > 2.8 AGGREGATES FOR CONCRETE > TABLE - 9 GRADING OF COARSE AGGREGATES
S029 [materials] PART 2 - PRODUCTS > 2.8 AGGREGATES FOR CONCRETE > TABLE - 10 / GRADING OF FINE AGGREGATES
S030 [materials] PART 2 - PRODUCTS > 2.8 AGGREGATES FOR CONCRETE > TABLE - 11 / ALL-IN-AGGREGATE GRADING
S031 [materials] PART 2 - PRODUCTS > 2.8 AGGREGATES FOR CONCRETE > TABLE - 12 / MOISTURE CONTENT & BULKING PERCENTAGE RELATION FOR SAND
S032 [materials] PART 2 - PRODUCTS > 2.9 MISCELLANEOUS MATERIALS
S034 [production_curing] PART 2 - PRODUCTS > 2.11 REQUIREMENTS FOR MASS CONCRETE
S036 [production_curing] PART 3 - EXECUTION
S037 [production_curing] PART 3 - EXECUTION > 3.1 GENERAL
S038 [production_curing] PART 3 - EXECUTION > 3.2 EXAMINATION
S039 [production_curing] PART 3 - EXECUTION > 3.3 PREPARATION
S045 [cover_sampling] PART 3 - EXECUTION > 3.5 REINFORCEMENT
S048 [cover_sampling] PART 3 - EXECUTION > 3.5 REINFORCEMENT > F. Cover to Reinforcement
S049 [production_curing] PART 3 - EXECUTION > 3.6 CONCRETE
S051 [production_curing] PART 3 - EXECUTION > 3.6 CONCRETE > F. Laying of Concrete
S052 [production_curing] PART 3 - EXECUTION > 3.6 CONCRETE > G. Compaction of Concrete
S053 [production_curing] PART 3 - EXECUTION > 3.6 CONCRETE > H. Construction joints
S055 [production_curing] PART 3 - EXECUTION > 3.6 CONCRETE > P. Curing
S058 [cover_sampling] PART 3 - EXECUTION > 3.9 FIELD QUALITY CONTROL
S059 [cover_sampling] PART 3 - EXECUTION > 3.9 FIELD QUALITY CONTROL > 7. Acceptance of Work
S060 [cover_sampling] PART 3 - EXECUTION > 3.10 INDEPENDENT TESTING
```

Not selected (full list also in `output/not_selected.txt`):

```
S000 PART 1 - GENERAL   (no body text)
S001 PART 1 - GENERAL > 1.1 SUMMARY
S006 PART 1 - GENERAL > 1.3 SYSTEM DESCRIPTION > B. Sustainable Design [and LEED] Performance Criteria
S007 PART 1 - GENERAL > 1.4 SUBMITTALS
S010 PART 1 - GENERAL > 1.7 PROJECT/SITE CONDITIONS
S011 PART 2 - PRODUCTS   (no body text)
S012 PART 2 - PRODUCTS > 2.1 FORMWORK MATERIALS
S013 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES
S014 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties
S015 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > TABLE - 1 / MECHANICAL PROPERTIES OF MILD STEEL & MEDIUM TENSILE STEEL BARS
S015.T1 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > TABLE - 1 / MECHANICAL PROPERTIES OF MILD STEEL & MEDIUM TENSILE STEEL BARS > [TABLE] TABLE - 1 / MECHANICAL PROPERTIES OF MILD STEEL & MEDIUM TENSILE STEEL BARS / [IS 432 Table - 1]
S016 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > TABLE - 2 / CHEMICAL COMPOSITION OF HIGH STRENGTH DEFORMED BARS
S016.T1 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > TABLE - 2 / CHEMICAL COMPOSITION OF HIGH STRENGTH DEFORMED BARS > [TABLE] TABLE - 2 / CHEMICAL COMPOSITION OF HIGH STRENGTH DEFORMED BARS / [IS 1786]
S017 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > MECHANICAL PROPERTIES OF HIGH STRENGTH DEFORMED BARS AND WIRES
S017.T1 PART 2 - PRODUCTS > 2.2 REINFORCING STEEL BARS, WELDED STEEL WIRE FABRIC AND ACCESSORIES > C. Physical properties > MECHANICAL PROPERTIES OF HIGH STRENGTH DEFORMED BARS AND WIRES > [TABLE] MECHANICAL PROPERTIES OF HIGH STRENGTH DEFORMED BARS AND WIRES / [IS 1786 Table - 3]
S033 PART 2 - PRODUCTS > 2.10 CURING MATERIALS
S035 PART 2 - PRODUCTS > 2.12 REINFORCEMENT STEEL FABRICATION
S040 PART 3 - EXECUTION > 3.4 FORMWORK
S041 PART 3 - EXECUTION > 3.4 FORMWORK > B. Design of Formwork
S042 PART 3 - EXECUTION > 3.4 FORMWORK > E. Form Construction
S043 PART 3 - EXECUTION > 3.4 FORMWORK > F. Form Stripping And Reshoring
S043.T1 PART 3 - EXECUTION > 3.4 FORMWORK > F. Form Stripping And Reshoring > [TABLE] (no caption)
S044 PART 3 - EXECUTION > 3.4 FORMWORK > K. Cleaning and Treatment of Forms
S046 PART 3 - EXECUTION > 3.5 REINFORCEMENT > D. Lapping of Bars
S047 PART 3 - EXECUTION > 3.5 REINFORCEMENT > E. Spacing of Bars
S050 PART 3 - EXECUTION > 3.6 CONCRETE > E. Shrinkage cracks
S054 PART 3 - EXECUTION > 3.6 CONCRETE > L. Openings
S056 PART 3 - EXECUTION > 3.7 FINISHES FOR FORMED SURFACES
S057 PART 3 - EXECUTION > 3.8 FINISHES FOR FLATWORK
S061 PART 3 - EXECUTION > 3.10 INDEPENDENT TESTING > END OF SECTION   (no body text)
```

## 4. Extracted parameters vs audit

| Audit metric | Parameter | Extracted value | Source quote | Audit status |
|---|---|---|---|---|
| Concrete Type | `concrete_type` | Reinforced Concrete | Reinforced Concrete (applicable concrete type for this structure as stated in the instructions) | PASS |
| Environmental Exposure | `exposure` | Moderate | Moderate - for example, sheltered from heavy and wind driven rain and against freezing, whilst saturated with water; buried concrete in s... | PASS |
| Cement Type | `cement_type` | OPC | Cement shall be ordinary Portland cement conforming to IS 269 for all purpose unless specified differently. | PASS |
| Soil Total SO3 | `soil_total_so3_percent` | null |  | MISSING |
| Soil Extract SO3 | `soil_extract_2_1_so3_gl` | null |  | MISSING |
| Groundwater SO3 | `groundwater_so3_gl` | null |  | MISSING |
| Sulfate Cement Type | `cement_type` | OPC | Cement shall be ordinary Portland cement conforming to IS 269 for all purpose unless specified differently. | PASS |
| Freezing and Thawing | `freezing_thawing_exposure` | null |  | MISSING |
| Concrete Grade | `specified_grade` | null |  | MISSING |
| Min Cement Content | `specified_min_cement` | 290 | 290 | FAIL |
| Max Cement Content | `specified_max_cement` | null |  | MISSING |
| W/C Ratio | `specified_wc` | 0.55 | 0.55 | FAIL |
| Standard Deviation (sigma) | `specified_sigma` | null |  | MISSING |
| Characteristic Strength | `specified_characteristic_strength` | null |  | MISSING |
| Fire Resistance Rating | `fire_resistance_rating` | null |  | MISSING |
| Beams Cover | `member_covers.Beams` | null |  | MISSING |
| Columns Cover | `member_covers.Columns` | null |  | MISSING |
| Slabs Cover | `member_covers.Slabs` | null |  | MISSING |
| Mixing Time | `mixing_time_minutes` | 2 | The mixer shall be run for a minimum period of 2 minutes after all materials are loaded in full quantity. | PASS |
| Transportation Time | `transport_time_minutes` | null |  | MISSING |
| Compaction Method | `compaction_method` | mechanical vibrator | The Contractor shall provide concrete batch mixers, vibrators, weight batches conforming to relevant IS specification. | PASS |
| Curing Days | `curing_days` | 7 | Starting 24 hours after placement of the concrete, the surface shall be cured by flooding with water or covering with damp Hessian cloth ... | PASS |
| Slump | `specified_slump_mm` | null |  | MISSING |
| Formwork Removal - Walls/Columns | `formwork_* (skipped by design)` | Not Provided |  | MISSING |
| Formwork Removal - Slabs (props left under) | `formwork_* (skipped by design)` | Not Provided |  | MISSING |
| Formwork Removal - Beam Soffit (props left under) | `formwork_* (skipped by design)` | Not Provided |  | MISSING |
| Formwork Removal - Props Under Slabs | `formwork_* (skipped by design)` | Not Provided |  | MISSING |
| Formwork Removal - Props Under Beams/Arches | `formwork_* (skipped by design)` | Not Provided |  | MISSING |
| Cement Type (Cross-Reference) | `cross_references` | Deferred to IS 269 | Cement shall be ordinary Portland cement conforming to IS 269 for all purpose unless specified differently. | PASS |
| Water Testing (Cross-Reference) | `cross_references` | Deferred to IS 3025 | Water shall be tested in accordance with IS 3025. | PASS |
| Coarse Aggregate Grading (Cross-Reference) | `cross_references` | Deferred to IS 383 | Grading of coarse aggregate shall conform to the requirements in IS 383. | PASS |
| Fine Aggregate Grading (Cross-Reference) | `cross_references` | Deferred to IS 383 | Grading of fine aggregate shall conform to IS 383 and shall fall within limits of one of the four zones given in table 4 of IS 383. | PASS |
| Aggregate Deleterious Material Limits (Cross-Reference) | `cross_references` | Deferred to IS 383 | The maximum quantities of deleterious materials in the coarse aggregate ... shall not exceed the limits provided in Table -- 8. | PASS |
| Mix Design Approval (Cross-Reference) | `cross_references` | Deferred to IS 456 | The design shall be carried out strictly to IS specifications and IS code practice 456 | PASS |
| Mix Design Guidelines (Cross-Reference) | `cross_references` | Deferred to SP 23 | minimum cement content per cubic meter of reinforced concrete should not be less than that stipulated in table 23, 24, 25 and 26 of SP 23 | PASS |
| Mix Design Guidelines (Cross-Reference) | `cross_references` | Deferred to SP 24 | minimum cement content per cubic meter of reinforced concrete should not be less than that stipulated in table 23, 24, 25 and 26 of SP 23 | PASS |
| Trial Mix Testing (Cross-Reference) | `cross_references` | Deferred to IS 1199 | when tested according to Is 1199 and IS 2386 - Part III | PASS |
| Trial Mix Testing (Cross-Reference) | `cross_references` | Deferred to IS 2386 | when tested according to Is 1199 and IS 2386 - Part III | PASS |
| Cube Curing And Testing (Cross-Reference) | `cross_references` | Deferred to IS 516 | Cubes shall be cast, stored, cured, transported and tested per IS 516 | PASS |
| Water pH | `water_ph` | null |  | MISSING |
| Water - Organic Solids | `water_organic_mg_l` | 200.0 | Organic            \| 200 mg/l | PASS |
| Water - Inorganic Solids | `water_inorganic_mg_l` | 3000.0 | Inorganic          \| 3000 mg/l | PASS |
| Water - Sulphates | `water_sulphates_mg_l` | 500.0 | Sulphates (as SO4) \| 500 mg/l | FAIL |
| Water - Chlorides | `water_chlorides_mg_l` | 1000.0 | Chlorides (as C1)  \| 2000 mg/l for plain concrete work and 1000 mg/l for reinforced concrete work | FAIL |
| Water - Suspended Matter | `water_suspended_matter_mg_l` | 2000.0 | Suspended matter   \| 2000 mg/l | PASS |
| Chloride Content | `measured_chloride_content` | null |  | MISSING |
| Sulphate (SO3) Content | `measured_so3_percent` | null |  | MISSING |
| Total Volume | `total_volume_m3` | null |  | MISSING |
| Cube Size | `sampling_cube_size_mm` | null |  | MISSING |
| Sampling Sets | `specified_sampling_sets` | null |  | MISSING |

Note: `exposure` and `concrete_type` are given from outside (CLI args), as in the app. The auditor fills in `exposure`='Moderate' and `cement_type`='OPC' defaults when they are null, so 'Cement Type' can show PASS even without an extracted value; check the value column.

Cross-references extracted:

- cement_type -> IS 269: "Cement shall be ordinary Portland cement conforming to IS 269 for all purpose unless specified differently."
- water_testing -> IS 3025: "Water shall be tested in accordance with IS 3025."
- coarse_aggregate_grading -> IS 383: "Grading of coarse aggregate shall conform to the requirements in IS 383."
- fine_aggregate_grading -> IS 383: "Grading of fine aggregate shall conform to IS 383 and shall fall within limits of one of the four zones given in table 4 of IS 383."
- aggregate_deleterious_material_limits -> IS 383: "The maximum quantities of deleterious materials in the coarse aggregate ... shall not exceed the limits provided in Table -- 8."
- mix design approval -> IS 456: "The design shall be carried out strictly to IS specifications and IS code practice 456"
- mix design guidelines -> SP 23: "minimum cement content per cubic meter of reinforced concrete should not be less than that stipulated in table 23, 24, 25 and 26 of SP 23"
- mix design guidelines -> SP 24: "The design shall be carried out strictly to IS specifications and IS code practice 456, SP 23 and SP 24"
- trial mix testing -> IS 1199: "when tested according to Is 1199 and IS 2386 - Part III"
- trial mix testing -> IS 2386: "when tested according to Is 1199 and IS 2386 - Part III"
- cube curing and testing -> IS 516: "Cubes shall be cast, stored, cured, transported and tested per IS 516"

## 5. MISSING parameters - is the value in the document?

MISSING audit rows: 25. Params: `soil_total_so3_percent`, `soil_extract_2_1_so3_gl`, `groundwater_so3_gl`, `freezing_thawing_exposure`, `specified_grade`, `specified_max_cement`, `specified_sigma`, `specified_characteristic_strength`, `fire_resistance_rating`, `member_covers.Beams`, `member_covers.Columns`, `member_covers.Slabs`, `transport_time_minutes`, `specified_slump_mm`, `formwork_* (skipped by design)`, `water_ph`, `measured_chloride_content`, `measured_so3_percent`, `total_volume_m3`, `sampling_cube_size_mm`, `specified_sampling_sets`

Manual search of `output/clean.md` for each MISSING parameter (grep for the value wording, units and synonyms). "In localized.md / sent in call" was checked by grepping the exact source phrase in `output/localized.md` and `output/extract_calls/*.json`.

| Parameter | In the document? | Where / exact wording | In localized.md? Sent in call | Verdict |
|---|---|---|---|---|
| `transport_time_minutes` | **Yes** | 3.6 F. Laying of Concrete: "Concrete shall be placed in position within 30 minutes from the time it is produced." (Also 1.7 hot-weather: "reduce the mixing/delivery time from 11/2 hrs. to 1-1/4 hrs.") | Yes (S051), call extract[8]. The 1.7 sentence is in S010, not selected (site conditions = OUT by scope) | **Extraction miss** |
| `specified_slump_mm` | **Yes** | 3.6 B.d: "The slump shall be 25 mm to 35 mm depending upon the location and type of Work." | Yes (S049), call extract[7] | **Extraction miss** |
| `water_ph` | **Yes** | 2.6 C.3: "The PH value of water shall not be less than 6 and more than 9." | Yes (S024), call extract[0] | **Extraction miss** |
| `measured_chloride_content` | **Yes, as a limit** | 2.7 A: "...not more than the limits for soluble chloride ion content in the specified standards or 0.6 kg/m 3 of concrete." | Yes (S026), call extract[0] | **Extraction miss** (the field is named "measured", but the auditor compares it with the IS 456 limit, so the spec's stated limit is what belongs here) |
| `sampling_cube_size_mm` | **Yes, indirectly** | 2.3 Table 4 NOTE 1: "...specified characteristic compressive strength of 15 cm cube at 28 days"; 2.6 C.1: "three 15 cm concrete cubes". The sampling clauses (3.9 / 3.10) say "6 cubes" but give no size | Yes (S019, S024), calls extract[4] / extract[0] | **Extraction miss (borderline)**: 150 mm is stated, but not in the sampling clause itself |
| `specified_sampling_sets` | Rule only | 3.9 / 3.10 tables: "Up to 5 cu.m. in a day: 1 ... More than 50 cu.m.: 4 + one additional per each 50 cu.m." | Yes (S058, S060), calls extract[9] / extract[10] | **Not resolvable**: the count depends on `total_volume_m3`, which the doc does not give |
| `total_volume_m3` | No | No project quantity anywhere ("cu.m." appears only in the sampling-frequency tables) | - | **Truly absent** (project data, not spec data) |
| `member_covers.Beams/Columns/Slabs` | By reference | 3.5 F.1: "thickness of such cover shall be as specified in the Drawings or as directed by the ER"; F.2: cover not reduced by more than 5 mm | Yes (S048), call extract[9] | **Stated only by reference (drawings)** |
| `specified_grade` | By reference / list only | 2.3 A: grades "shall be as shown in Table 4" (a list M10-M60); Table 4 NOTE 3: "Grades of concrete lower than M 15 shall not be used in reinforced concrete." No single specified grade | Yes (S018, S019), call extract[4] | **No single value; by reference** (only a minimum, M15, is stated) |
| `specified_characteristic_strength` | No single value | Table 4 maps every grade to fck; with no specified grade there is no single fck | Yes (S019) | **Follows grade, so not determinable** |
| `specified_max_cement` | No | No maximum cement content clause ("450" / "maximum cement" not found) | - | **Truly absent** |
| `specified_sigma` | No | "standard deviation" not found | - | **Truly absent** |
| `fire_resistance_rating` | No | "fire" appears only in reference-list titles (IS 1641/1642/1643/3809) | - | **Truly absent** |
| `freezing_thawing_exposure` | No | "freezing" appears only inside the Table 5 exposure-class descriptions | - | **Truly absent** |
| `soil_total_so3_percent`, `soil_extract_2_1_so3_gl`, `groundwater_so3_gl` | No | Table 6 gives only the class thresholds (requirements), with no site soil or groundwater test values | - | **Truly absent** (site investigation data) |
| `measured_so3_percent` | No | Only "Do not use any admixtures which contain chlorides or sulphates." No SO3 number | - | **Truly absent** |
| `formwork_*` (5 audit rows) | (not checked) | - | - | **Skipped by design** (step 4 returns null) |

**Summary of the 20 non-formwork MISSING rows:**
- 5 are **extraction misses**: transport time, slump, water pH, chloride limit, cube size. The value is in localized.md and was sent to the model.
- **0 localization misses** for the primary statement of any parameter. One secondary statement was not selected: the 1.7 hot-weather "1-1/4 hrs" delivery time, which sits in a site-conditions section that the scope marks OUT.
- 5 are **stated only by reference or as a rule**: covers x3 (drawings), grade (list / Table 4), sampling sets (volume-dependent rule).
- 10 are **truly absent**: soil/groundwater SO3 x3, freezing, max cement, sigma, fire rating, SO3 content, total volume, and characteristic strength (follows the missing grade).

**Related wrong-value finding (not MISSING):** `specified_wc` = 0.55 came from the Table 5 lookup (Moderate / RC). However, 3.6 B.d states "The water cement ratio shall be between 0.5 to 0.52." That sentence went to call extract[7] (production_curing), which returned null for `specified_wc`. The table value fills the field, but the clause that actually governs the mix was not extracted.

## 6. Audit counts

| Status | Count |
|---|---:|
| PASS | 21 |
| FAIL | 4 |
| MISSING | 25 |
| WARNING | 0 |
| total ledger rows | 50 |

auditor.py's own counts (MISSING is counted as 'warning' there): {'pass': 21, 'fail': 4, 'warning': 25, 'total': 50}

## 7. Fallback hook

`experiments/fallback_search/keywords.json` found: **True**. The fallback search itself is not implemented. Null params it would hand over: water_ph, measured_chloride_content, measured_so3_percent, freezing_thawing_exposure, soil_total_so3_percent, soil_extract_2_1_so3_gl, groundwater_so3_gl, specified_grade, specified_max_cement, specified_characteristic_strength, specified_sigma, transport_time_minutes, specified_slump_mm, total_volume_m3, specified_sampling_sets, sampling_cube_size_mm, fire_resistance_rating, member_covers.Beams, member_covers.Columns, member_covers.Slabs.

