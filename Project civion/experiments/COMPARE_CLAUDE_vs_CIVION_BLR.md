# Civion V1 / V2 / V4 vs Claude Opus 5.5 (chat) — BLR spec, Moderate exposure, RCC

**Part A (below):** the original BLR spec, few real errors. **Part B (end of file):** Claude medium without IS code on a BLR spec with many
manually seeded errors. The two cases are kept apart on purpose.

## Setups compared
| Name | What it is |
|---|---|
| V1 | Civion pipeline v1: section picking + chunked extraction, then deterministic audit |
| V2 | Civion pipeline v2: routing + one extraction call per parameter group, then deterministic audit |
| V4 | Civion pipeline v4: one Gemini call on the whole document, Python reads grading tables, then deterministic audit |
| Claude medium | Claude Opus 5.5, medium effort, input = BLR spec only (IS values from the model's own knowledge) |
| Claude medium + IS (run 1, run 2) | Claude Opus 5.5, medium effort, input = BLR spec + IS 456:2000 + IS 383:2016 PDFs, told to take IS values from the PDFs; run twice |
| Claude high + IS | Claude Opus 5.5, high effort, same input and instruction as medium + IS |

Civion setups extract values; the audit against `database.py` (IS values) is deterministic. Claude setups do both
extraction and the PASS/FAIL judgement in one answer.

**Ground truth.** Where V2, V4 and Claude agree, the value is taken as correct. Every disagreement was checked in
the BLR spec (Docling Markdown); IS values were checked in the IS 456:2000 and IS 383:2016 PDFs.

**The 35 parameters.** 31 are single values (member cover counts as 3: beams, columns, slabs). 4 are tables:

| Table parameter | Values inside | Claude splits it into |
|---|---:|---:|
| aggregate_deleterious_limits (6 items × 4 aggregate types) | 18 | 6 rows |
| coarse_aggregate_grading (10 sizes × 9 sieves) | 42 | 9 rows |
| fine_aggregate_grading (4 zones × 7 sieves) | 28 | 7 rows |
| all_in_aggregate_grading (2 sizes × 6 sieves) | 11 | 6 rows |

Each table counts as one parameter; it is correct only if every value in it is correct.

## 1. Results

| | V1 | V2 | V4 | Claude medium | Claude medium + IS, run 1 | Claude medium + IS, run 2 | Claude high + IS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Extraction accuracy (35 fields) | 61.4 % | 84.3 % | **100 %** | **100 %** | **100 %** | **100 %** | **100 %** |
| Values found, of 24 stated in the spec | 10.5 | 18.5 | 24 | 24 | 24 | 24 | 24 |
| Values invented where the spec is silent (11) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Compliance status accuracy, strict | 68.6 % (24/35) | 85.7 % (30/35) | **100 % (35/35)** | 85.7 % (30/35) | 94.3 % (33/35) | 94.3 % (33/35) | 94.3 % (33/35) |
| Compliance status accuracy, incl. defensible* | 68.6 % | 85.7 % | **100 %** | 97.1 % (34/35) | **100 % (35/35)** | **100 % (35/35)** | **100 % (35/35)** |
| Wrong verdicts | 11 | 5 | **0** | 1 | **0** | **0** | **0** |
| Wrong IS requirement values stated | 0 | 0 | 0 | 4 | 0 | 0 | 0 |
| Source quotes verified verbatim by code | partly | yes | yes | no | no | no | no |
| Token use | ~42k | 77,034 | 42,288 | **129,307 in + 24,789 out** (output includes thinking) = 154,096 (measured) | **500,780 in + 19,807 out** (output includes thinking) = 520,587 (measured; 5–6 % of Pro session) | 5–6 % of Pro session | **500,780 in + 21,982 out** (output includes thinking) = 522,762 (measured) |

Scoring: correct = 1; partial = 0.5 (right value but incomplete). Every setup is scored on the same 35
parameters. Where Claude splits a table parameter (deleterious limits, gradings) into several rows, the parameter
counts as correct only if all its rows are correct.
\* Defensible = Claude answered UNCLEAR (or FAIL with a valid reason) where the spec itself is ambiguous,
e.g. cubes vs cylinders, no single grade (see 3).

## 2. Extraction — fields where the setups differ
All other fields are identical in every setup.

| Field | Correct (BLR) | V1 | V2 | V4 | Claude (all 4) |
|---|---|---|---|---|---|
| transport_time_minutes | 30 min (3.6.F.6); 90 min delivery also stated (1.7.A.3) | not found | 30 | 30, 90 in remark | 30, 90 noted |
| specified_wc | 0.55 (Table 5) and 0.50–0.52 (3.6.B.1.d) | 0.55 | 0.55, both in remark | 0.50–0.52, both in remark | both |
| curing_days | 7 + 7 = 14 | 7 (½) | 14 | 14 | 14 |
| specified_slump_mm | 25–35 | not found | 25–35 | 25–35 | 25–35 |
| water_ph | 6–9 | not found | 6–9 | 6–9 | 6–9 |
| measured_chloride_content | 0.6 kg/m³ (2.7.A) | not found | not found | 0.6 | 0.6 |
| sampling_cube_size_mm | 150 | not found | not found | 150 | 150 |
| sampling_frequency | table in 3.10.E.2.a | not in schema | took the copy with typing errors (½) | correct table | correct table |
| member_covers (beams, columns, slabs) | refers to Drawings | not found ×3 | reference ×3 | reference ×3 | reference ×3 |
| aggregate_deleterious_limits (18 cells) | Table 8 | not in schema | 18/18 | 18/18 | all |
| coarse / fine / all-in grading (42 / 28 / 11 cells) | Tables 9–11 | reference to IS 383 only | reference to IS 383 only | 42/42, 28/28, 11/11 | all |

V1 and V2 had no instruction to add remarks for a second stated value; V4's prompt asks for them, so V4 reports
both values for transport time and w/c ratio.

## 3. Compliance status — where Claude differs from the correct verdict

| Row | Correct (checked in IS PDF) | Claude medium | Medium + IS run 1 | Medium + IS run 2 | High + IS |
|---|---|---|---|---|---|
| Deleterious, total, crushed coarse aggregate: spec 5.00 vs IS 2.00 | FAIL | PASS ✗ | FAIL ✓ | FAIL ✓ | FAIL ✓ |
| Concrete grade: spec assigns no grade; allows ≥ M15 in RCC; IS needs ≥ M25 (Moderate) | MISSING | FAIL (defensible) | FAIL (defensible) | FAIL (defensible) | FAIL (defensible) |
| Cube size 150 mm (spec also mentions cylinders in 3.10.E) | PASS | UNCLEAR (defensible) | PASS ✓ | PASS ✓ | PASS ✓ |
| Sampling sets (total volume not given) | MISSING | UNCLEAR (defensible) | UNCLEAR (defensible) | UNCLEAR (defensible) | UNCLEAR (defensible) |
| Sampling frequency (bands match IS 456 15.2.2) | PASS | UNCLEAR (defensible) | PASS ✓ | PASS ✓ | PASS ✓ |

V4 reports the crushed-coarse total as FAIL, the grade and sampling sets as MISSING, and cube size and
sampling frequency as PASS.

**IS requirement values Claude medium (spec only) stated wrongly** (verdict not affected except the crushed-coarse
total; V4 takes all these from `database.py`). The + IS setups made none of these errors.
- Slab cover: "25 mm if bars ≤ 12 mm" — IS 456 Table 16 Note 2 allows the 5 mm reduction for Mild exposure only.
- Mixing time: "IS gives no numeric minimum" — IS 456 cl 10.3.1 says at least 2 min.
- Deleterious, crushed coarse total "5.00" — IS 383 Table 2 says 2.00.
- Graded 40 mm and 20 mm coarse aggregate at the nominal sieve: "same as IS" — IS 383 Table 7 says 90–100, spec says 95–100 (still PASS).

## 4. Observations
1. **V4 and Claude + IS reach the same accuracy.** Both extract all 35 fields correctly and give no wrong verdict.
   V4 is 100 % strict; Claude + IS is 94.3 % strict only because it marks the grade FAIL (spec floor M15 vs
   IS M25) and sampling sets UNCLEAR where V4 says MISSING — both are fair calls.
2. **Grounding in the IS code is what matters.** Without the IS PDFs, Claude medium made 4 IS-value mistakes and
   1 wrong verdict (IS 383:2016 Table 2 changed from the 1970 edition). With the PDFs: none. V4 gets the same
   grounding from its checked rule base (`database.py`), with no IS text sent to the model.
3. **Effort and cost:** adding the IS PDFs raised Claude's usage from 154,096 tokens (measured) to about 520k
   tokens, i.e. from 3 % to 5–6 % of a Pro session. Medium + IS →
   high + IS gave no accuracy gain and used about the same share (5–6 %). Exact tokens are known for one medium + IS
   run (500,780 input + 19,807 output incl. thinking = 520,587) and for the high + IS run (500,780 input + 21,982
   output incl. thinking = 522,762): high effort added about 2,200 output tokens (≈ 0.4 % of the total). Both are
   about 12× V4's 42,288 for the same 100 % extraction accuracy.
4. **Repeatability:** Claude medium + IS run 1 and run 2 gave the same verdict on every scored row; V4 run twice also
   gave the same verdict on all 38 audit rows.
5. **Where V4 is ahead:** quotes checked verbatim by code, fixed status labels (PASS / FAIL / MISSING / REFERENCE;
   Claude uses INFO, UNCLEAR, "—" and varies row splits), one API call with measured tokens (42k, spec only), and
   the output is machine-readable JSON for the audit.
6. **What Claude adds:** it points out conflicts inside the spec (30 vs 90 min, w/c 0.55 vs 0.50–0.52, cubes vs
   cylinders, duplicated sampling table with typing errors, −5 mm cover tolerance vs IS +10/−0 mm, spec clause 1.7.B
   citing IS 456 cl 13.4 which is now construction joints, tables copied from IS 456:1978 and IS 383:1970).
   V4 reports the first two in remarks.

## 5. Token use
Civion counts are measured from the API. Claude chat on a Pro plan shows only the share of the current session
used (medium spec only 3 %; medium + IS 5–6 % per run; high + IS 5–6 %). Exact token counts of the compliance call
are available for the runs below (Claude Opus 5.5). **Medium, spec only (BLR as PDF, no IS codes): input 129,307,
output 24,789 (includes thinking), 154,096 in total** (about 3.6× V4's 42,288). With input = BLR spec + IS 456 +
IS 383 as PDFs: **medium + IS: input 500,780, output 19,807 (includes thinking),
520,587 in total**; **high + IS: input 500,780, output 21,982 (includes thinking), 522,762 in total**. The other
medium + IS run was not measured.

**Documents sent as Markdown instead of PDF** (BLR spec + IS 456 + IS 383, all three as Markdown files; only the token
count was measured, the output was not compared): **input 210,569, output 28,339 (includes thinking), 238,908 in
total**. Input is 58 % lower than with PDFs (500,780), but output is higher, so the total is 54 % lower
(238,908 vs about 521k). It is still about 5.7× V4's 42,288. For context: the BLR spec is ≈ 30k tokens; IS 456 has 114 pages and
IS 383 has 22, and Claude + IS reads these in addition to the spec, which is why its input is more than 10× V4's.

## 6. Notes and limitations
1. **Test document.** The check used the real BLR specification, with no errors added by hand. For Civion this is
   enough: the audit after extraction is deterministic, so only extraction needs testing. For Claude, which also
   does the IS comparison itself, one document is a light test of that step. BLR has 6 real violations
   (min cement, w/c, water sulphates, water chlorides, two deleterious limits); Claude's only wrong verdict came
   from the less familiar IS 383:2016 values when it worked from its own knowledge.
2. **Why no seeded-error document yet.** Claude with the IS PDFs (medium and high) gave no wrong verdict here, so
   more errors are not expected to change that much. The risk sits with runs that take IS values from the model's
   own knowledge, which may PASS cases that should FAIL. A document with many seeded errors is planned as the next test.
3. **Scaling.**
   - Claude: a real compliance check may need many IS codes and long specifications in one chat. Every run re-reads
     the full codes although only a few clauses are needed, so usage grows with each code and page, and context
     and plan limits are reached sooner. Measured for BLR with two codes: 500,780 input tokens (high + IS).
   - Civion: the IS values are stored once in a targeted database (`database.py`) and reused; each check sends only
     the spec (≈ 42k tokens for BLR). The cost is manual effort to build the database for each new code, and only
     parameters in the database are checked.
   - Expected: at scale, Civion stays cheaper and more consistent per check; Claude stays more flexible (it also
     reports issues outside the fixed parameter list, see 4.6).

---

# Part B — Claude medium, no IS code, on a BLR spec with many seeded errors

Document: `SPEC DOC/big_error_BLR_Airport_Cast-in-Concrete_error_version.pdf` (BLR spec with many manually seeded errors).
Claude Opus 5.5, medium effort, spec only, no IS PDFs, Moderate exposure, Reinforced Concrete. All IS values come from the model's
memory. Output: `Opus_5.5_medium_big_error_BLR_without_IS_Code_Civion_test.md`.

The question: can the model run the complete check on its own, with no IS code supplied? Two things were checked: whether each extracted
value matches the document, and whether the IS requirement Claude states and its PASS / FAIL are right (IS values checked against
IS 456:2000 and IS 383:2016).

## B1. Results
| | Claude medium, no IS |
|---|---:|
| Compliance accuracy, incl. defensible* | 91.4 % (32/35) |
| Compliance accuracy, strict | 85.7 % (30/35) |
| Wrong parameters | 3: slab cover, crushed coarse total, compaction (see B3) |
| Wrong verdicts | 1 (compaction) |
| Errors in the document | 30 |
| Errors found | 28 (24 as FAIL, 4 in a remark) |
| Errors missed or wrong | 2 (crushed coarse total, compaction) |
| Extraction accuracy (35 parameters) | 100 %: every extracted value matches the document, including all changed table cells |
| Values invented where the spec is silent (11) | 0 |
| Token use | **129,307 in + 24,789 out** (output includes thinking) = 154,096, copied from the earlier BLR run of this setup, not re-measured |

\* **This is not a verdict-only score.** A parameter is counted wrong if its extracted value, the IS requirement Claude states, or its status is wrong,
even when the final status looks right. That is why slab cover (wrong IS value, status still REFERENCE), crushed coarse total (wrong IS value) and
compaction (wrong status and IS statement) count as wrong. Defensible = UNCLEAR or FAIL with a valid reason where the spec is ambiguous: grade (FAIL; the spec only
sets an M20 floor, IS needs M25) and sampling sets (UNCLEAR; total volume not stated). Strict also counts those two as wrong.
(Scored on the final status alone it would be 97.1 % incl. defensible, 91.4 % strict.)
Claude's own count (61 rows): PASS 22 · FAIL 22 · MISSING 10 · REFERENCE 3 · UNCLEAR 2 · INFO 2.

## B2. Every error in the document and what Claude did
✓ = found and failed with the right IS reason.

| # | Error in the document | Claude |
|---|---|---|
| 1 | Minimum cement, Moderate RCC: 240 kg/m³ (IS 300) | ✓ |
| 2 | Table 5 Note 1 allows a 25 % cement reduction (IS 456 allows none) | found in a remark |
| 3 | w/c: Table 5 0.60 and clause 3.6 0.65–0.72 (IS max 0.50) | ✓ |
| 4 | Concrete grade: spec floor M20, no member grade (IS needs M25) | FAIL (defensible) |
| 5 | Table 4 strengths M20 = 22, M25 = 20, M40 = 45, basis "10 cm cube at 14 days" | ✓ |
| 6 | Cube size 10 cm (IS 150 mm) | ✓ |
| 7 | Water pH minimum 3 (IS 6) | ✓ |
| 8 | Water organic 450 mg/l (IS 200) | ✓ |
| 9 | Water inorganic 3500 mg/l (IS 3000) | ✓ |
| 10 | Water sulphates 500 as SO4 (IS 400 as SO3, about 480 as SO4) | ✓ |
| 11 | Water suspended matter 4500 mg/l (IS 2000) | ✓ |
| 12 | Chloride content 0.8 kg/m³ (IS 0.6) | ✓ |
| 13 | Deleterious, fine uncrushed finer than 75 µm: 8.00 (IS 3.00) | ✓ |
| 14 | Deleterious, clay lumps fine crushed: 4.00 (IS 1.00) | ✓ |
| 15 | Deleterious, total coarse uncrushed: 9.00 (IS 5.00) | ✓ |
| 16 | Deleterious, coarse finer than 75 µm: 3.00 (IS 1.00 for every coarse type) | found in a remark: "possibly ~1 %, verify" (the IS value is 1.00, so ~1 % is right) |
| 17 | Deleterious, total crushed coarse aggregate: 5.00 (IS 383:2016 Table 2: 2.00) | **missed. Wrong IS value:** Claude stated the IS limit as 5.00, so the spec's 5.00 looked compliant and was not flagged (same issue in Part A). The row is FAIL only because of the other changed cells |
| 18 | Coarse grading, 63 mm single at 40 mm sieve: 0–60 (IS 0–30) | ✓ |
| 19 | Fine grading, Zone I 2.36 mm: 40–95 (IS 60–95) | ✓ |
| 20 | Fine grading, Zone II 600 µm: 35–79 (IS 35–59) | ✓ |
| 21 | Fine grading, Zone IV 150 µm: 0–35 (IS 0–15) | ✓ |
| 22 | All-in grading, 40 mm at 4.75 mm: 25–65 (IS 25–45) | ✓ |
| 23 | Cover may be reduced by 15 mm (IS +10 / −0 tolerance) | found in a remark |
| 24 | Slump 150–250 mm (IS 456 cl. 7.1 bands are at most 100–150) | ✓ |
| 25 | Mixing time minimum 1 minute (IS 2 min) | ✓ |
| 26 | Compaction "hand ramming only" (IS 456 cl. 13.3.1: concrete shall be compacted using mechanical vibrators, so FAIL) | **wrong. Not failed:** it should be FAIL, but Claude marked UNCLEAR, saying cl. 13.3 has no list of prohibited methods (wrong IS statement) |
| 27 | Mass-concrete curing 4 days | found in a remark ("would fail") |
| 28 | Clause 3.8 sampling table, 30–50 m³: 2 samples (IS 4) | ✓ |
| 29 | Clause 3.10 sampling table, 5–15 m³: 1 sample (IS 2) | ✓ |
| 30 | Clause 3.10, above 50 m³: one extra per 100 m³ (IS per 50 m³) | ✓ |
| 31 | *Not a document error:* slab cover (the spec only refers to the drawings, so there is nothing to fail) | **Claude's IS value wrong.** Claude stated "25 mm allowed for bars up to 12 mm in Moderate exposure". IS 456 Table 16 allows that 5 mm reduction for Mild exposure only (same issue in Part A). The status stayed REFERENCE, so it did not change a verdict, but it is counted as a wrong parameter |

30 errors (rows 1–30): 28 found, 2 missed or wrong (rows 17, 26). Row 31 is Claude's own mistake, not an error in the document.

## B3. Parameters Claude got wrong (3 of 35)
These count as wrong even where the final status happened to look right, because Claude's stated IS requirement or status was wrong.

| Parameter | What Claude did | Correct | Effect on the status |
|---|---|---|---|
| Member cover (slab) | Said "25 mm allowed for bars up to 12 mm in Moderate exposure" | IS 456 Table 16 allows that reduction for Mild exposure only (same issue in Part A) | None: the row is a reference to the drawings, so the wrong IS value did not change the status |
| Aggregate deleterious limits | Stated the IS limit for total crushed coarse aggregate as 5.00 | IS 383:2016 Table 2: 2.00 (same issue in Part A) | The spec's 5.00 looked compliant, so that error was missed; the row is FAIL only because of other cells |
| Compaction | Said IS 456 cl. 13.3 has no list of prohibited methods; marked "hand ramming only" UNCLEAR | Cl. 13.3.1 requires mechanical vibrators, so FAIL | Wrong status |

Every other IS value Claude stated was right (min cement 300, w/c 0.50, M25, chloride 0.6, water limits, mixing ≥ 2 min, curing 7 / 10 days, slump bands,
IS 383 grading limits, sampling bands of cl. 15.2.2, coarse aggregate finer than 75 µm about 1 %).

## B4. What happened
1. **Three of the 35 parameters are wrong** (slab cover, crushed coarse total, compaction), although the final status of two of them (slab cover, the deleterious row) still looks right.
2. Every numeric limit error was caught (water, cement, w/c, slump, mixing, cube size, aggregate tables, sampling): 28 of 30 errors found.
3. The 2 errors not caught are the crushed coarse total (row 17, wrong IS value) and hand ramming (row 26, marked UNCLEAR instead of FAIL after a wrong reading of IS 456 cl. 13.3).
4. Extraction matched the document.

## B5. Conclusion
1. **With many errors in the spec and no IS code supplied, Claude's comparison is where the problems appear.** It read every value correctly, but the IS
   requirements it recalled from memory were sometimes wrong (slab cover, crushed coarse total, compaction clause), so a violation was missed,
   a status was wrong, and three of the 35 parameters count as wrong. Without the standard in front of it, the model can state a requirement that is not in the code.
2. **Extraction is not the weak point.** Extraction needs an LLM, since there is no other way to read a free-form specification, and it is
   accurate enough here: every value in the spec, including every changed table cell, was read correctly.
3. **That is where CIVION differs by design.** The LLM is used only for extraction. The comparison with the IS code is a deterministic pipeline against
   `database.py`, so the IS requirement values are fixed, checked values and cannot be misremembered, and the PASS / FAIL logic is the same on every run.
   For this reason V4 was not run on this document: its comparison accuracy does not need testing, only its extraction does. Once a value is extracted,
   the check on every parameter in the database follows from the rule base, however many errors the spec contains. V4's result is therefore expected to be the same
   as in Part A (not run here).
4. **Tokens.** Claude without IS PDFs used 154,096 tokens on this kind of spec (measured on the earlier BLR run; not re-measured on this document).
   Giving Claude the standards as documents is the way to get better results (Part A: no wrong verdicts with the PDFs), but it raised use to about 520,000 tokens
   for just two codes (IS 456 and IS 383), against about 42,000 for V4, which sends only the specification.
5. **Scaling.** A real compliance check needs many standards, not two. For Claude, token use rises with every code uploaded, and the chance of a wrong or
   unsupported answer is expected to rise with it (not measured here). For CIVION, token use stays at the size of the specification. The cost is human effort:
   the deterministic pipeline and `database.py` have to be built for each standard first, and only parameters in the database are checked. Once built,
   it is expected to hold a clear advantage in hallucination risk and token use as the number of standards grows.

## B6. Where CIVION is limited
CIVION expects each parameter in a fixed, structured form (a single value, a range, a table). The LLM fills that structure and the deterministic audit then
checks it. If a specification states the same parameter in a form the pipeline does not expect, the input cannot be accepted until the input types, the database
and the audit are extended to handle it. V4 is already flexible in several cases (a parameter can be accepted as either a single value or a range), but covering
most specifications means studying how each parameter is written across many technical specifications. That is a large amount of human work, and some forms
will still be missed. Claude, as a general LLM with no fixed format, accepts any layout without this work. That is its advantage. CIVION's advantage is the
deterministic comparison, fixed checked IS values and much lower token use (B5).
