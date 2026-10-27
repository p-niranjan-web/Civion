# How requirements appear in BLR - catalogue (Part 2, read-only)

Source read in full: `experiments/pipeline/output/clean.md` (the cleaned Docling text of the BLR spec,
1,068 lines). "Line" = line number in that file. "BLR clause" = the spec's own numbering, only to help
find the text; nothing below depends on it.

Columns:
- **Shape** - how the requirement is written (see the shape list at the end).
- **Now** - can today's schema (parser.py / groups.py fields) + database.py hold it, and does auditor.py check it?
  `audited` = field exists and is compared with IS; `field only` = extracted but the check is not a real
  IS comparison; `REFERENCE` = handled by the new reference status; `no` = nothing represents it.
- **IS basis** - whether IS 456 / IS 383 has a number to compare with (my reading; values marked "?" need
  your confirmation before they go into database.py).

BLR's run2 extraction/audit result is given where it matters.

## 1. Grades and strength

| Line | BLR clause | Requirement (short) | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 413-431 | 2.3 A, Table 4 | Grade designations M10...M60 and their characteristic strengths (10...60 N/mm2) | **set of values** (grade -> fck), a reference table, not "the grade of this structure" | no (field `specified_grade` is one grade; prompt correctly returns null for a list) | IS 456 Table 2: fck = number in the grade name. Auditable as a set (each row fck == grade number) |
| 433 | Table 4 note 1 | Grade number = strength of 15 cm cube at 28 days | text (gives cube size 150 mm indirectly) | `sampling_cube_size_mm` (MISSING in run2) | IS 456 cl 6.1 / IS 516: 150 mm cube |
| 435 | Table 4 note 3 | Grades lower than M15 shall not be used in reinforced concrete | **one-sided limit (min)**, general rule | no (no "min grade for RC" field) | IS 456:2000 Table 5: minimum M20 for RC (mild). BLR's M15 would FAIL |
| 834 | 3.6 B.1.a | Grades as in Table 2 of IS 456 / Table 4 | reference only (IS 456) | REFERENCE | - |
| - | - | No grade is stated for the actual structure anywhere | (absent) | `specified_grade` MISSING (correct) | - |

## 2. Durability / exposure

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 447-453 | 2.4, Table 5 | Min cement content and max w/c per exposure (3 classes: Mild/Moderate/Severe) x plain/reinforced | **table lookup** (exposure x concrete type -> value) | audited (`specified_min_cement` 290 FAIL vs 300, `specified_wc` 0.55 FAIL vs 0.50) | IS 456 Table 5 (has 5 classes and min grade; BLR's table is the older 3-class one) |
| 455 | Table 5 note 1 | Cement content may be reduced 10 % when w/c strictly controlled | conditional rule (adjustment) | no | not in IS 456:2000 Table 5 (relaxation does not exist there) - not auditable as a number |
| 456 | Table 5 note 2 | Min cement content based on 20 mm aggregate; -10 % for 40 mm, +10 % for 12.5 mm | conditional rule (adjustment by aggregate size) | no | IS 456 Table 5 note 2 has a similar adjustment (? exact wording/values to confirm) |
| 464-469 | 2.4, Table 6 | Sulphate classes 1-3: SO3 ranges -> cement type, min cement, max free w/c | **table lookup** keyed by measured site values (soil/groundwater SO3) | partly: database has Table 4, but site SO3 comes from outside the document; BLR's own table rows are not extracted | IS 456 Table 4 (KNOWN_ISSUES #3: database class 2 is collapsed) |
| 315 | 1.7 B | Concreting in aggressive soils per 13.4 of IS 456 | reference only | REFERENCE (if extracted) | - |
| 836-838 | 3.6 B.1.c | Min cement content not less than SP 23 tables 23-26 and Tables 5/6 | reference only (internal + SP 23) | REFERENCE | - |
| - | - | Freezing and thawing: only mentioned inside exposure-class descriptions | (absent as a requirement) | MISSING (correct) | - |

## 3. Cement

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 473 | 2.5 A | Cement shall be OPC conforming to IS 269 | **category** (one allowed type) + reference | audited only as "must be defined" (`cement_type` OPC) | IS 456 cl 5.1 list of permitted cements |
| 475-482 | 2.5 C | Other cements allowed with approval: 43/53 grade OPC, PSC, PPC (fly ash / calcined clay), SRC, each "conforming to IS xxx" | **list of allowed categories**, each with a reference | no (only one `cement_type`); run2 put "IS 8112" in cross_references | IS 456 cl 5.1: all six are permitted types -> auditable as "every listed type is in the IS-permitted set" |
| 473 | 2.5 A | Cement stored over 4 weeks must be re-tested; bags of 50 kg | text / single value with no IS limit | no | not in IS 456 -> not auditable |
| 474 | 2.5 B | Storage: 15-20 cm above floor, 25-35 cm from walls, max 12 bags high | ranges / max | no | IS 4082 (not in scope) -> not auditable |
| 303 | 1.6 A.1 | Do not store bagged cement over 6 months (conflicts with 4 weeks above) | one-sided limit | no | not in IS 456 |
| 655 | 2.11 A | Mass concrete: moderate heat, moderate sulphate-resistance cement | category (conditional on mass concrete) | no | no IS 456 number |

## 4. Water

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 487 | 2.6 B | Water tested per IS 3025 | reference only | REFERENCE (run2: "water_testing -> IS 3025") | - |
| 489 | 2.6 C.1 | 28-day strength of cubes with this water >= 90 % of distilled-water cubes (three 15 cm cubes) | **one-sided limit (min %)** | no | IS 456 cl 5.4.1.1 (a): not less than 90 % |
| 490 | 2.6 C.2 | Initial setting time >= 30 min and within +/-30 min of control | **one-sided limit (min)** + **tolerance (+/-)** | no | IS 456 cl 5.4.1.1 (b): not less than 30 min, not differ by +/-30 min |
| 491 | 2.6 C.3 | pH not less than 6 and not more than 9 | **range** | audited as min only (`water_ph` 6.0 PASS) | IS 456 cl 5.4.2: pH >= 6 (no upper limit in IS 456 - upper bound not auditable) |
| 499-505 | Table 7 | Organic 200, inorganic 3000, sulphates 500, chlorides 2000 plain / 1000 RC, suspended 2000 mg/l | **set of values** (substance -> max), one row needs concrete type | audited as 5 separate fields (sulphates 500 FAIL vs 400, chlorides 1000 FAIL vs 500) | IS 456 Table 1 / cl 5.4 |

## 5. Admixtures and fly ash

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 509 | 2.7 A | Admixtures conform to IS 9103 (+ ASTM); use per IS 456 and IS 9103 | reference only | REFERENCE if extracted | - |
| 509 | 2.7 A | Calcium chloride and thiocyanates not permitted | **list of prohibited categories** | no | no explicit IS 456 prohibition (? to confirm) |
| 509 | 2.7 A | Chloride ion content of concrete not more than 0.6 kg/m3 | **one-sided limit (max)** | field exists (`measured_chloride_content`) but MISSING in run2 (the sentence is under admixtures, not routed/extracted) | IS 456 Table 7: RC 0.6 kg/m3 -> would PASS |
| 509 | 2.7 A | All structural concrete shall contain a water-reducing admixture | text (category required) | no | no IS 456 number |
| 510-516 | 2.7 B | Admixture classes (accelerators, retarders...) | list (informative) | no | not a requirement |
| 518 | 2.7 D | Fly ash per IS 3812; ignition loss max 6 %; max 220 kg/m3 | reference + one-sided limits | no | IS 3812 (not in scope) -> reference only |
| 219 | 1.3 B.2.b | Fly ash content above 30 % but within IS 1489 | one-sided limit + reference | no | IS 1489 (not in scope) |

## 6. Aggregates (IS 383)

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 526, 540 | 2.8 A.1, B.4 | Hard, durable, clean, cubical, no harmful materials... | text | no | IS 383 general clauses - not auditable as numbers |
| 527, 541, 555-565 | 2.8 A.2, B.5, Table 8 | Deleterious materials max % (coal/lignite, clay lumps, finer than 75 um, soft fragments, shale, total) for fine/coarse x crushed/uncrushed | **set of values** (substance x aggregate kind -> max %) | no | IS 383 Table 1 (1970 numbering) - values need confirming (see open question 2) |
| 567-569 | Table 8 notes | Mica: investigate; organic impurities: relative mortar strength not less than 95 % | text + one-sided limit (min %) | no | IS 383 note (? to confirm) |
| 528 | 2.8 A.3 | Crushing, impact, abrasion value and soundness per IS 383 paras 3.3-3.6 | reference only | REFERENCE if extracted | IS 383 has numbers, but BLR states none -> reference is the right result |
| 529, 575-586 | 2.8 A.4, Table 9 | Coarse aggregate grading: sieve -> % passing range, per nominal size (single-sized 63/40/20/16/12.5/10, graded 40/20/16/12.5) | **set of values (ranges)** keyed by nominal size; plus reference to IS 383 | reference only (run2: coarse_aggregate_grading -> IS 383 REFERENCE); the table values are not extracted | IS 383 Table 2 (1970) / Table 7 (2016). database.py has only the 20 mm single-sized column |
| 536, 543, 594-602 | 2.8 B.1, B.7, Table 10 | Fine aggregate grading zones I-IV: sieve -> % passing range | **set of values (ranges)** keyed by zone; plus reference | reference only | IS 383 Table 4 (1970) / Table 9 (2016) |
| 604 | Table 10 note 1 | Crushed stone sand: 150 um limit raised to 20 % | conditional single value | no | IS 383 note (? to confirm) |
| 610 | Table 10 note 4 | Zone IV not in RC unless tested | conditional category rule | no | IS 383 note - text |
| 553, 618-626 | 2.8 D, Table 11 | All-in aggregate grading 40 / 20 mm | **set of values (ranges)** | no | IS 383 Table 5 (1970) / Table 10 (2016) |
| 532 | 2.8 A.7 | Coarse aggregate specific gravity min 2.6 (SSD) | one-sided limit (min) | no | no IS 383 limit (? confirm) -> not auditable |
| 546-550 | 2.8 C.1-4 | Nominal aggregate size by usage: general 20; footings/mats/walls > 300 mm 40; tight pours 12.5 or 10; fill 12.5 | **table lookup** (usage -> size), values are allowed categories | no | IS 383 standard nominal sizes (40, 20, 16, 12.5, 10) -> auditable as "each size is a standard IS 383 size"; IS 456 cl 5.3.3 max size vs member thickness needs member dimensions -> not auditable |
| 551 | 2.8 C.5 | Fine aggregate for concrete fill: 100 % passing 4.75 mm, max 5 % passing 0.15 mm | set of values (one-sided per sieve) | no | applies to fill, not structural; IS 383 zone limits differ (? whether to audit) |
| 552 | 2.8 C.6 | Sand fineness modulus 2.50-3.00 | **range** | no | IS 383 gives no FM limit (? confirm) -> not auditable |
| 544, 632-637 | 2.8 B.8, Table 12 | Bulking vs moisture content | informative table | no | not a requirement |
| 797-802 | 3.5 E | Bar spacing >= 5 mm + nominal max aggregate size; vertical >= 15 mm | conditional rule (reinforcement detailing) | no | IS 456 cl 26.3.2 - outside the listed scope (reinforcement) |

## 7. Curing

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 938-939 | 3.6 P.1-2 | Begin protection 1-2 h after placing; from 24 h, 7 days flooding/hessian, then a further 7 days sprinkling | **single value** (total days) but split across two sentences | audited (`curing_days` 7 PASS; the group rule asks for the total, 14 - run2 took 7) | IS 456 cl 13.5.1: >= 7 days OPC, >= 10 days with mineral admixtures / dry hot weather |
| 940 | 3.6 P.3 | Mass concrete: 14 days | **conditional single value** (applies to mass concrete only) | no | IS 456 has no separate mass-concrete curing period (? confirm) |
| 941, 651 | 3.6 P.4, 2.10 | Membrane curing per 12.5 of SP 24; curing compound ASTM C1315 | reference only | REFERENCE if extracted | - |

## 8. Mass concrete

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 655 | 2.11 A | Applies to mats and footings > 1.0 m thick | conditional definition | no | no IS 456 number |
| 657 | 2.11 A.1 | Retardation min 3 hours | one-sided limit | no | no IS 456 number |
| 658 | 2.11 A.2 | Temperature max 21 C at deposit | one-sided limit | no | not IS 456 (IS 7861) -> not auditable now |
| 1003, 1039 | 3.8 / 3.10 | One additional sample tested at 56 days | conditional rule | no | not IS 456 |

## 9. Mixing, transport, placing, compaction, slump, w/c

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 831 | 3.6 A | Mechanical mixer; hand mixing only with permission | category (method) | no | IS 456 cl 10.3 (? hand-mixing 10 % extra cement rule to confirm) |
| 863 | 3.6 D.1 | Weight batching preferred; volume batching with approval | category | no | IS 456 cl 10.2 (? confirm) |
| 866 | 3.6 D.4 | Mixer run min 2 minutes after loading | one-sided limit (min) | audited (`mixing_time_minutes` 2 PASS) | database says IS 456 cl 10.3, 2 min - pre-existing value, I could not confirm it is in IS 456:2000 |
| 895 | 3.6 F.6 | Placed within 30 minutes of production | one-sided limit (max) | audited (`transport_time_minutes` 30 PASS) | database: 30 min, IS 456 cl 13.1 - pre-existing, not confirmed |
| 311 | 1.7 A.3 | Above 32 C reduce mixing/delivery time from 1 1/2 h to 1 1/4 h | conditional one-sided limit (conflicts with 30 min) | no (rule says ignore hot-weather value) | no IS 456 number |
| 312, 874 | 1.7 A.4, 3.6 D.8 | Placing temperature max 35 C / max 34 C | one-sided limit | no | IS 7861 (not in scope) |
| 890-896 | 3.6 F | Free fall max 1.5 m (columns/walls) / 2.5 m | one-sided limit | no | no IS 456 number |
| 900 | 3.6 G.1 | Compaction by vibrators | category | audited (`compaction_method` PASS) | IS 456 cl 13.3 |
| 839 | 3.6 B.1.d | w/c between 0.5 and 0.52 | **range** | partly: `specified_wc` took 0.55 from Table 5; the 0.52 candidate is in `conflicts` | IS 456 Table 5 max 0.50 (Moderate RC) -> 0.52 FAIL either way |
| 839 | 3.6 B.1.d | Slump 25-35 mm; higher with plasticizers | **range** | audited as upper bound (35 PASS vs 25-150) | IS 456 cl 7.1 workability table (database WORKABILITY values: pre-existing, ? confirm) |
| 907-909 | 3.6 H.2 | Construction joint spacing max 18 m / 6 m / 27 m | one-sided limits | no | no IS 456 number |
| 848-849 | 3.6 C.3-4 | Trial mixes: 5 cubes from each of 3 batches; avg of 3 >= specified, one may be lower but >= 90 % | conditional rule | no | IS 456:2000 uses target mean strength (cl 9.2) - criteria differ, needs a rule shape |

## 10. Cover

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 806 | 3.5 F.1 | Cover as specified in the Drawings or as directed by the ER | **reference only (non-code)** | REFERENCE (Part 1) - run2 had no such entry; the next run should produce it | - |
| 811 | 3.5 G.2 | Cover not reduced by more than 5 mm of that specified | **tolerance (one-sided, minus side)** | no | IS 456 cl 26.4.2: nominal cover +10 mm / 0 mm -> minus 5 mm would FAIL (? confirm) |
| 809-810 | 3.5 G.1 | Bar position tolerance +/-10 mm (d <= 200 mm), +/-15 mm (d > 200 mm) | **table lookup** (effective depth band -> tolerance) | no | IS 456 cl 12.3.2 (? confirm) |
| 641 | 2.9 A | Cover blocks: non-corrosive; strength at least that of the concrete | text + one-sided | no | IS 456 cl 26.4.? - text, not a number |
| - | - | Fire resistance rating not stated | (absent) | MISSING (correct) | - |

## 11. Sampling and acceptance

| Line | BLR clause | Requirement | Shape | Now | IS basis |
|---|---|---|---|---|---|
| 994-999, 1030-1036 | 3.8 / 3.10 E.2.a | Sampling frequency: up to 5 m3 -> 1, 5-15 -> 2, 15-30 -> 3, 30-50 -> 4, > 50 -> 4 + 1 per 50 m3 | **conditional / volume-based rule** given as a table (stated twice; the first copy is garbled by Docling) | no: schema expects one project volume + one number of sets (both MISSING) | IS 456 cl 15.2.2 - database SAMPLING_FREQUENCY. Auditable by comparing BLR's bands with IS bands row by row |
| 990, 1028, 1001, 1038 | same | Each sample = 6 cubes; 3 tested at 7 days, 3 at 28 days | single values | no | IS 456 cl 15.4: 3 specimens at 28 days (? confirm wording) |
| 848 | 3.6 C.3 | Cubes cast/cured/tested per IS 516 | reference only | REFERENCE | - |
| 1007-1014, 1042-1050 | 7 a / E.2.d | Acceptance: avg of 3 consecutive >= specified; no individual < 90 %; > 33 % below = freak | conditional rule | no (database CHARACTERISTIC_STRENGTH is a different, single-number check) | IS 456:2000 Table 11 uses 4 non-overlapping results and fck + 0.825 sigma / fck - 4 (? confirm) -> needs a rule shape |
| 1062 | 3.10 F | Slump test first truck each day, each sample | frequency rule | no | not IS 456 |

## 12. Out of the listed scope (seen, not catalogued in detail)

Reinforcement steel (Tables 1-3, IS 432/1786 properties), lapping (line 788: no lap splices for bars > 36 mm,
IS 456 cl 26.2.5.1), formwork (stripping table line 738-743 - formwork is out of scope for this work),
tolerances of formwork, finishes, LEED/green-building items, submittal deadlines.

## Shapes found

| Shape | Example in BLR | Count (approx.) |
|---|---|---|
| single value | mixing 2 min; curing 7 (+7) days | 4 |
| one-sided limit (min / max) | chloride <= 0.6 kg/m3; water strength >= 90 %; setting >= 30 min; spec. gravity >= 2.6 | 12 |
| range | w/c 0.5-0.52; slump 25-35; pH 6-9; FM 2.5-3.0 | 4 |
| tolerance (+/-, or one side) | setting time +/-30 min; cover -5 mm; bar position +/-10/15 | 3 |
| table lookup (value depends on exposure / type / size / depth) | Table 5; Table 6; aggregate size by usage | 4 |
| set of values (named items, each with its own limit) | water solids Table 7; deleterious Table 8; grade -> fck Table 4 | 3 |
| set of ranges (sieve -> % passing min-max) | coarse/fine/all-in grading Tables 9-11 | 3 |
| list of allowed / prohibited categories | permitted cement types; no calcium chloride | 3 |
| conditional / volume-based rule | sampling bands; acceptance criteria; mass-concrete-only values | 5 |
| reference only - IS code | IS 383 grading; IS 3025; IS 516; IS 9103 | ~10 |
| reference only - non-code | cover "as specified in the Drawings" | 1 (concrete scope) |
| text / descriptive | aggregate cleanliness, storage, finishes | many |

## What BLR states that we cannot represent today

1. Aggregate tables: deleterious limits (Table 8), coarse/fine/all-in grading (Tables 9-11), aggregate size by
   usage, FM, specific gravity, fine aggregate for fill.
2. Water suitability tests: 90 % strength, initial setting time >= 30 min / +/-30 min.
3. Cover tolerance (-5 mm) and bar-position tolerance by depth.
4. Minimum grade for reinforced concrete (M15 note) and the grade -> fck table.
5. Permitted cement type list (only one `cement_type` exists).
6. Sampling frequency stated as a rule table (schema wants one volume + one count, which a spec rarely gives).
7. Number of cubes per sample / test ages; acceptance criteria.
8. Mass-concrete-only values (curing 14 days, 21 C, 3 h retardation).
9. Ranges keep only one bound (pH upper bound, w/c lower bound, slump lower bound are dropped).

## Stated but not auditable against IS 456 / IS 383 (no IS number, or other code)

Cement storage limits; placing temperatures (IS 7861); free-fall heights; construction-joint spacing;
mass-concrete definition/temperature/retardation; fly ash limits (IS 3812/IS 1489); FM and specific gravity
(? confirm IS 383 has none); pH upper bound 9; hot-weather delivery time; slump-test frequency;
water-reducing admixture mandatory; Table 5 note 1 (10 % reduction).

## Open questions for you (before Part 3)

1. **IS 383 edition.** database.py cites IS 383:2016 (Table 7). BLR cites the 1970 numbering (Tables 1, 2,
   4, 5). The grading values I remember are the same in both editions, and they match BLR, but the
   deleterious-materials table changed in 2016. Which edition is ground truth? Can you give me the IS 383
   tables (PDF or values) so I do not use BLR's numbers or my memory?
2. **IS values I am not certain of** (need your confirmation or the code text): IS 383 deleterious limits
   (e.g. "material finer than 75 um" for coarse aggregate: 1 % or 3 %?), crushed-sand 150 um note (20 %),
   organic-impurity 95 % rule; IS 456 cl 26.4.2 cover tolerance (+10/0 mm); cl 12.3.2 bar-position
   tolerances; cl 5.4.1.1 water tests (90 %, 30 min, +/-30 min); cl 15.4 specimens per sample;
   Table 11 acceptance criteria.
3. **Pre-existing database values I could not confirm** (I will not change them without your word):
   mixing time 2 min (cl 10.3), transport 30 min (cl 13.1), WORKABILITY slump bands.
4. **Scope:** include reinforcement-detailing items (lap splice <= 36 mm bars, bar spacing) or keep them out
   as the list in the task suggests?
5. **Mass-concrete values and other "conditional" requirements:** audit only when IS has a number (so mostly
   not), or record them as extras (Part 3.3)?
