# CHANGES: pipeline v1 -> v2

The v1 snapshot is commit `843df8b` ("pipeline v1", branch `pipeline-localization`); its outputs are copied in `v1_results/`. v2 writes each run to `output_v2/<run>/`.

## Reused from v1 (unchanged logic)
- `clean.py`: image-marker removal, HTML-entity decoding, repeated header/footer rule.
- `sections.py`: heading split, hierarchy inference, table detection and captions, outline. The v1 audit found every non-empty clean.md line in exactly one section (793/793).
- `localize.py`: the Stage A outline-only call (same prompt, medium reasoning) and the "picked child -> keep parent text" rule.
- `common.call_groq`: JSON mode, temperature 0, measured `usage` logging, sliding-window TPM pacing (7,000/min), 429 retry with backoff.
- The null-parameter hook for the future keyword fallback (still not implemented).
- `auditor.run_civion_audit(result, IS456_MASTER)`, called the same way.

Signature-only change: `sections.main` and `localize.main` now take `out_dir`, so runs do not overwrite each other.

## Fixed (bugs found in the Part 0 audit of v1)
1. **Invented source quote.** v1 stamped `exposure`/`concrete_type` with `setdefault`, so the model-written quote "Reinforced Concrete (applicable concrete type ... as stated in the instructions)" was kept, and that text is not in the document. v2 always overwrites both quotes with "determined outside the document".
2. **Bare-number quotes.** v1 quotes such as "290" and "0.55" are technically in the document but prove nothing. The v2 prompt requires a whole sentence or a whole table row.
3. **Wrong quote in the v1 report.** The cross-reference rows matched quotes by parameter name only, so the SP 24 row showed the SP 23 quote. v2's report lists cross-references with their own quotes.
4. **Localization misses (checked by reading clean.md).** Not selected in the v1 run, but in scope:
   - `2.10 CURING MATERIALS` (curing compound);
   - `3.6 E. Shrinkage cracks` (covering after placement, hot-weather placing);
   - `1.7 PROJECT/SITE CONDITIONS`, which actually holds hot/cold-weather concreting (delivery time 1-1/4 h above 32 °C, placing temperature, IS 456 13.4 for aggressive soils). The scope rule "site/project conditions = OUT" excludes it by title.

   v2 adds two deterministic safety nets after Stage A: descendants of a picked section that has its own text, and sections whose heading contains a generic scope cue word. Routing then drops anything pulled in by mistake. 1.7 is still not caught, because its title has no cue word. This is documented, not hidden.
5. **Silent merge.** v1 kept a `_candidates` map but silently chose a value. v2 records every disagreement in `extraction["conflicts"]` and the report.
6. **Silent failure on Groq HTTP 400 `json_validate_failed`.** Found during v2's first run attempt (log kept in `output_v2_run1_attempt1_failed.log`). v1 code turned the error into "0 ids selected", and the run continued with an empty Stage A. Now `call_groq` retries this error up to 2 times (without the fixed seed), and `run_v2.py` stops if Stage A selects nothing.
8. **v2 regression, found and fixed between run1 and run2.** My first v2 extraction prompt narrowed parser.py's cross-reference rule to deferrals "for one of these parameters". Every call in run1 returned `cross_references: []`, even though the IS 383 / IS 269 units were routed correctly (v1 found 11). run2 uses parser.py's CROSS-REFERENCES paragraph verbatim.
7. **Quote checking.** New `verify.py` does a deterministic check of every quote against clean.md. It tolerates Docling's stray "- " list markers inside a sentence, which made the SP 23 quote look missing when it was not.

Checked and found correct (no change): clean.py found no header/footer lines to remove in this doc (no line repeats 3+ times once images are gone). The 4 v1 FAILs (min cement 290, w/c 0.55, water sulphates 500 mg/l, water chlorides 1000 mg/l) are real differences from database.py, which is the ground truth. The spec reproduces older SP 23 values. Every v1 value quote except `concrete_type` was found in clean.md and supports its value.

## New in v2
- `groups.py` / `groups.md`: 5 fixed, document-independent parameter groups (26 parameters, each in exactly one group). Formwork and externally supplied fields are excluded. Adding a parameter is one `P(...)` line.
- `units.py`: splits in-scope sections into clause/table units (tables carry caption + rows; long clauses split at sub-clauses; tiny pieces merged).
- `route.py`: scope safety nets + Stage B routing. Batched calls tag each unit (path + ~300-char preview or table caption/header/rows, plus cue words found later in the unit) with the groups it feeds. Multi-tag is allowed, ids the model skips are retried once, and anything still missing goes to all groups. Writes `scope.json`, `units.json`, `routing.json` (unit -> groups, per-group token counts).
- `extract_v2.py`: one call per group with only that group's fields and rules plus only its routed units (document order, heading paths), split into batches under ~5,000 tokens. Merge prefers non-null and records conflicts.
- `run_v2.py`, `report_v2.py`, `verify.py`.

## Known open issues after v2 (not fixed)
- Routing over-tags (by design: "when unsure, tag more"). The materials group gets about 45 units / 11k EST tokens, so v2 costs more tokens than v1.
- Routing is not stable: 28% of common units got different tags between run1 and run2.
- Batch conflicts are recorded, not resolved: w/c 0.55 (table) vs 0.52 (mix-design clause).
- Per-field rules in groups.py are not always followed (curing 7+7 days returned 7).
- Composed table quotes (row label + column header + cell) fail the verbatim check, although the values are right.
- `1.7 PROJECT/SITE CONDITIONS` (hot-weather concreting) is still out of scope.
