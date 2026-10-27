# Shapes / references work - final report

Branch `pipeline-localization`. Ground truth = IS 456:2000 and IS 383:2016 PDFs in `Project civion/IS Codes/`
(no value copied from a specification). MEASURED = counted by code or by the Groq API usage field.

## Commits

| Commit | What |
|---|---|
| 4565572 | before shapes/reference work (snapshot; `.env` not committed) |
| 8888225 | REFERENCE status (backend) |
| fc50c0a | REFERENCE badge + quote + summary line in the UI |
| 0b8467c | table values quoted as header row + data row; verify.py checks it |
| 795cbc9 | transport-time and workability entries fixed against IS 456 |
| a4b0111 | shape-driven audit (database.py PARAMETERS, auditor.py one check per shape, IS 383:2016 tables) |
| c45f8a7 | Ledger shows the extraction remark |
| c821823 | pipeline: cell-by-cell table merge, multi-row table quotes, TLS opt-in, `--input`, run3 |
| (final) | run4, doc coverage, token section, this report |

## What changed, per file

- **database.py** - `PARAMETERS`: one entry per audited field (metric, shape, unit, clause, `limit` or
  `limit_from` path into the IS tables with `{exposure}` / `{concrete_type}` / `{cement_type}`). `SHAPES`
  documents each shape. `IS383_2016`: Tables 2, 7, 9, 10, typed from the IS 383:2016 page images. Fixes:
  transport time has no IS 456 limit (cl 13.1); workability bands per cl 7.1. Formwork and all other
  existing entries untouched.
- **auditor.py** - rewritten around `PARAMETERS`: `resolve_limit()`, one `check_<shape>()` per shape, four
  single-use rules (cover, strength window, sampling count, sulphate cement); REFERENCE for any missing
  field with a `cross_references` entry; remarks copied onto rows; each ledger row carries `Field`. Formwork
  checks moved into a function unchanged. Why: adding a parameter is now data, not code.
- **prompt_rules.py** (new) - rules shared by parser.py and the pipeline: references, table quotes, remarks,
  and the IS 383 group/item names read from database.py.
- **parser.py** - schema: ranges allowed for w/c, slump, pH; 4 aggregate fields; `sampling_frequency`;
  `remarks`; shared rules.
- **experiments/pipeline** - groups.py: range rules, `aggregates` group, `sampling_frequency`.
  extract_v2.py: remarks (model + automatic on conflicts), cell-by-cell merge for table fields, padding
  squeezed, `extract_group()` shared with rerun_groups.py. verify.py: table quotes (header row + data
  row(s) of the same table). common.py: opt-in `CIVION_CLASSIC_TLS=1`. run_v2.py: `--input`.
- **Frontend** (approved) - Ledger: REFERENCE badge, quote, remark; Dashboard: summary line.
- **test_dummy_audit.py** - cases per shape + schema-sync check.
- **HOW_TO_ADD_PARAMETER.md** (repo root), **STATUS.md**.

## Shapes

`defined`, `min`, `max`, `range`, `equals`, `not_in`, `set_max`, `set_range`, `sampling`
(+ single-use `cover`, `strength_window`, `sampling_count`, `sulphate_cement`). A stated range is judged by
its worst end (min -> low end, max -> high end, range -> both ends inside). Any shape -> REFERENCE when the
value is missing and the document points to a code or the drawings.

## New parameters

`aggregate_deleterious_limits` (IS 383 Table 2), `coarse_aggregate_grading` (Table 7),
`fine_aggregate_grading` (Table 9), `all_in_aggregate_grading` (Table 10), `sampling_frequency`
(IS 456 cl 15.2.2 as bands).

## Tests (MEASURED)

`python test_dummy_audit.py`: **40 of 40 as expected** (pass/fail/missing per shape, REFERENCE, remark,
schema sync). Regression old vs new auditor on the dummy input and on BLR run2: every existing row has the
same status except the intended changes (sampling count above 50 m3: 100 m3 now needs 5, IS 456
cl 15.2.2 - the old code asked for 6).

## BLR before / after (run2 = before, run4 = after; same v2 pipeline, extended)

Details: `run2_vs_run4.md`, `run2_vs_run3.md`.

| | run2 | run4 |
|---|---|---|
| Audit (current auditor) | 18 pass, 4 fail, 25 missing, 5 ref (47 rows) | 20 pass, 5 fail, 19 missing, 6 ref (44 rows) |
| Summary line | 38 % passed, of which 5 are references | 45 % passed, of which 6 are references |
| Quotes found in document | 2 table quotes failed | 20 of 20 (9 of 9 table quotes) |
| Tokens / calls | 61,954 / 18 | 77,034 / 20 |

Changes in extracted values: w/c 0.55 kept, with remark "0.55 vs 0.5-0.52"; slump 35 -> [25, 35];
pH 6 -> [6, 9]; curing 7 -> 14 (7 + 7 days); cover -> REFERENCE (drawings, 3 rows); deleterious limits
18/18 cells correct -> FAIL (coarse finer than 75 um 3 % vs IS 1 %; coarse crushed total 5 % vs 2 %);
sampling_frequency -> PASS (see caveat below).

Token split per step for v1, v2 run1/run2, run3, run4: `experiments/pipeline/report_v2.md` section 7.

## Could not verify

1. **Coarse grading (11-column table)**: misread by the LLM - run3 29/38 cells correct (shifted
   columns), a one-field-per-call retry was worse; run4 returned REFERENCE instead. Not working.
2. **Fine and all-in grading**: correct in run3 (28/28, 11/11 cells) but run4 returned REFERENCE
   ("as per IS 383") instead of the table. Works, not reliably.
3. **sampling_frequency**: read from Docling's garbled first copy of the table (5-15 m3 band lost,
   up-to-5 band shows 2). PASS is right for BLR's intent but the extracted bands are partly wrong.
4. **NMP Noida / Colombo**: not run (NMP section picking failed: Groq json_validate_failed x3; skipped as
   agreed). `doc_coverage.md` is from reading; NMP fine grading zone III FAIL was confirmed by feeding the
   hand-typed table to the auditor.
5. **App path** (parser.py): not run end-to-end; its prompt still cuts the document at 12,000 chars, so
   aggregate tables are usually not reached there.

## Open questions

1. **Wide tables**: proposal - the LLM only identifies the table and which column is which designation;
   Python reads the cells. Build it?
2. **Table vs reference**: when a document has both "as per IS 383" and its own table, prompt should
   say "extract the table". Small prompt change; not tested (Groq budget). OK to add?
3. **References to non-IS codes** (BS 882, ASTM): counted as PASS like IS references. Keep, or show them
   as Warning ("not an IS reference")?
4. **Extras list** (Part 3.3, not built): `{name, value, unit, quote}` for requirements with no field,
   not audited, collapsed UI section. Build?
5. **Curing with PPC/PSC**: IS 456 cl 13.5.1 asks 10 days for blended cements; the curing table has no
   PPC/PSC key, so 7 days is used. Add PPC/PSC = 10?
6. Untouched known issues: default exposure/cement make "must be defined" always pass (KNOWN_ISSUES #2);
   sulphate class 2 (#3); the characteristic-strength check is not IS 456 Table 11 (kept unchanged).
7. **TLS**: on the current network Python's default TLS handshake to Groq times out (OpenSSL 3.5);
   the pipeline has an opt-in workaround, the app's client does not.
