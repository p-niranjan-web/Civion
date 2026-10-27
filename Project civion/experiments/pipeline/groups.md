# Extraction groups (v2) - rationale

Source of the parameter list: the JSON schema in `parser.py`'s prompt, cross-checked against what `auditor.py` reads and the rule tables in `database.py`. The code lives in `groups.py`; adding a parameter means adding one `P(...)` line to one group.

## Excluded on purpose
- **Formwork** (`formwork_removal_hours`, `formwork_removal_days`, `formwork_span_m`): out of scope for this pipeline, returned as null.
- **Supplied from outside the document**, as in the app: `exposure`, `concrete_type` (CLI args), and the site soil/groundwater sulphate values `soil_total_so3_percent`, `soil_extract_2_1_so3_gl`, `groundwater_so3_gl`. These are site-investigation data, not specification requirements. They stay null unless supplied.

## The 5 groups (26 parameters, each in exactly one group)

| Group | Parameters | Why together |
|---|---|---|
| `grade_strength` | specified_grade, specified_characteristic_strength, specified_sigma | All three are read from the grade/strength clauses and grade tables. Strength and sigma only make sense next to the grade (IS 456 cl. 6, 9.2). |
| `durability` | specified_min_cement, specified_max_cement, specified_wc, freezing_thawing_exposure, measured_chloride_content, measured_so3_percent | IS 456 cl. 8 (Table 5/Table 4 and the 8.2.5 chloride/sulphate limits). The values usually sit together in an exposure/sulphate table or a mix-proportioning clause, and one table often feeds several of these fields. |
| `materials` | cement_type, water_ph, water_organic/inorganic/sulphates/chlorides/suspended_mg_l | IS 456 cl. 5: material clauses (cement, water quality table). Keeping the 5 water fields with pH puts the whole water-quality table in one call, so it is resolved once. |
| `production` | mixing_time_minutes, transport_time_minutes, compaction_method, specified_slump_mm, curing_days | IS 456 cl. 10-13: workmanship. These are scattered across many short "execution" clauses (mixing, transport, placing, compaction, curing). Grouping them lets routing pull in only those clauses. |
| `cover_sampling` | member_covers, fire_resistance_rating, sampling_cube_size_mm, specified_sampling_sets, total_volume_m3 | Cover with fire rating (fire rating drives the cover requirement in the auditor), and the sampling fields with volume (the sampling-set rule depends on volume; cl. 15). |

`cross_references` is not a parameter: every group's call may return deferrals to other codes, and they are merged and deduplicated.

## Rules that differ from parser.py's prompt
These per-parameter rules are generic, but they were **motivated by v1 failures on the BLR document**, so they carry some risk of overfitting. Validate them on the held-out documents:
- Range handling: for max-type fields (w/c, slump) use the upper bound; for min-type fields (cement content, pH) use the lower bound.
- `specified_wc`: a ratio stated in a mix-design clause takes priority over a general exposure-table value.
- `curing_days`: consecutive periods of moist curing are added together.
- `transport_time_minutes`: use the general limit, not a hot-weather reduction.
- `freezing_thawing_exposure`: an exposure-class description that merely mentions freezing is not a statement.
- `specified_grade`: a reference table that lists every possible grade does not count as specifying a grade.

## Cues
Each parameter carries a few plain cue words, used only as a routing hint. route.py lists which cues occur in the part of a unit that is NOT shown to the router (beyond the first ~300 chars). They are never used to extract values.
