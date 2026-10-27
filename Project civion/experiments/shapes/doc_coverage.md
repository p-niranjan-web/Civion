# Parameter x document coverage

Documents (Docling markdown in experiments/parse_test/docling_samples/):
- **BLR** = BLR Airport (Cast-in-Concrete) - IS-based. **MEASURED**: pipeline run4 (+ run3), every value
  checked against the document (quotes: verify.py; table cells: check_tables_blr.py).
- **NMP** = NMP Noida - IS-based. **READ ONLY**: the pipeline run failed at section picking (Groq
  json_validate_failed, empty output x3); entries below are from reading the text, not extraction.
- **COL** = Bandaranaike Airport Colombo - BS-based (BS 882, BS 1881, BS EN 1008). **READ ONLY**.

Legend: ✅ fits the schema and audits correctly · 🟡 fits, with a caveat · 🔗 reference ("as per IS/drawings")
· ❌ stated but our schema cannot hold it · — not stated (or not found).

| Parameter (field) | Shape | BLR (measured) | NMP (read) | COL (read) |
|---|---|---|---|---|
| specified_grade | min | — (only a grade list) | 🟡 grade table by member/use, no single grade | ❌ grade per member table (M15-M45) |
| specified_min_cement | min (Table 5 by exposure) | ✅ 290 -> FAIL vs 300 | ❌ min cement per *grade* table (not per exposure) | — |
| specified_max_cement | max | — | 🟡 "450 kg" appears only as a table cell | — |
| specified_wc | max (range = high end) | ✅ 0.55 FAIL + remark (0.5-0.52 also stated) | ✅ 0.50 max for ordinary concrete | — |
| specified_sigma | defined | — | 🟡 sigma table per grade (3.5/4/5/6) | — |
| characteristic strength | strength_window (unchanged) | — | — | — |
| cement_type | defined | ✅ OPC | ✅ OPC / fly-ash blended | 🟡 OPC (BS EN 197-1) |
| water_ph | min (range = low end) | ✅ [6, 9] PASS | ✅ 6.5-8.0 -> PASS | ✅ 7.0-9.0 -> PASS |
| water_organic / inorganic_mg_l | max | ✅ 200 / 3000 PASS | ❌ only total dissolved solids 2000 ppm | — |
| water_sulphates_mg_l | max | ✅ 500 FAIL vs 400 | ✅ 1000 ppm -> FAIL vs 400 | — |
| water_chlorides_mg_l | max (by concrete type) | ✅ 1000 FAIL vs 500 | ✅ 500 ppm (as Cl) -> PASS | — |
| water_suspended_matter_mg_l | max | ✅ 2000 PASS | ✅ 2000 ppm -> PASS | — |
| measured_chloride_content | max kg/m3 | — (0.6 kg/m3 stated under admixtures, not extracted) | ❌ % of cement (unit differs) | ❌ % of cementitious content |
| measured_so3_percent | max | — | — | — |
| mixing_time_minutes | min | ✅ 2 PASS | — | — ("specified mixing time", no number) |
| transport_time_minutes | defined | ✅ 30 | ✅ 30 min | — |
| compaction_method | not_in | ✅ vibrators PASS | ✅ high-frequency vibrators | — |
| curing_days | min | ✅ 14 (7+7) PASS | ✅ 10 days -> PASS | — (curing compound, no days found) |
| specified_slump_mm | range | ✅ [25, 35] PASS | ✅ 40-75 -> PASS | 🟡 min 75 design slump |
| member_covers | cover | 🔗 "as specified in the Drawings" (REFERENCE) | — | ❌ cover table per structural element, not beam/column/slab |
| fire_resistance_rating | defined | — | — | — |
| sampling_cube_size_mm | equals 150 | — (stated as "15 cm cubes" in notes; not extracted) | ✅ 150 mm | 🟡 100 or 150 mm by aggregate size |
| sampling_frequency | sampling (bands) | 🟡 PASS, but read from Docling's garbled first copy (5-15 m3 band lost); remark added | — | ❌ BS-style per-batch rule |
| total_volume / sampling_sets | defined / sampling_count | — | — | — |
| aggregate_deleterious_limits | set_max (IS 383 Table 2) | ✅ 18/18 cells correct; FAIL (coarse finer than 75 um 3 % vs 1 %) | 🟡 limits written as sentences (chloride, sulphate %), not Table 2 items | ❌ BS 882 |
| fine_aggregate_grading | set_range (IS 383 Table 9) | 🟡 run3: 28/28 cells correct, PASS; run4: model returned REFERENCE instead | ✅ zone table; zone III 600 um 35-60 vs IS 60-79 -> would FAIL | 🔗 BS 882 |
| coarse_aggregate_grading | set_range (IS 383 Table 7) | ❌ 11-column table misread (29/38 cells, shifted); run4: REFERENCE | 🔗 "as per IS 383" | 🔗 BS 882 |
| all_in_aggregate_grading | set_range (IS 383 Table 10) | 🟡 run3: 11/11 cells correct, PASS; run4: REFERENCE | — | — |
| cross_references (REFERENCE) | any | ✅ drawings + IS 383 + IS 3025 + IS 516 | ✅ many "as per IS 383 / IS 456" | 🟡 BS codes - would count as PASS (see open question) |

## What was done for the differences

- Ranges (pH 6-9, slump 25-35, w/c 0.5-0.52): one schema field takes a number or [low, high]; the
  auditor judges the worst end. Covers all three documents.
- "As per IS 383" instead of a table: the same field becomes REFERENCE. Covers BLR (some runs) and NMP.
- Two values for one field (BLR w/c): first in document order is audited, a remark shows both.
- Not built (would mean per-document structures): grade/cover per structural member (COL), min cement
  per grade instead of per exposure (NMP), chloride as % of cement (NMP, COL), BS-code aggregate rules (COL).
