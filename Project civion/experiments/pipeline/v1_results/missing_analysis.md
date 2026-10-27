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
