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

> **SCOPE OF THIS CHECK:** like the v1 analysis, this traces each parameter's primary statement. It does not audit what Stage A cropping dropped. Sections still out of scope in v2 include `S010` (1.7, hot-weather concreting) and `S057` (3.8 FINISHES FOR FLATWORK, which holds the "6 cubes" sampling clause under a misleading heading). v2's safety nets added 2.10 and 3.6 E but not these two. Verify with `output_v2/<run>/not_selected.txt`.
