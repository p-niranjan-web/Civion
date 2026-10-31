# Known issues & suggestions — compliance-check engine (`auditor.py` / `database.py`)

> **Note (2026-10-28):** the items below are known limitations of the current version. The project does not plan major changes to them; 2 of the 9 have been fixed (see the status line under each item).

> ⚠️ **DO NOT IMPLEMENT ANYTHING IN THIS FILE WITHOUT THE REPO OWNER'S EXPLICIT PERMISSION.**
> This is a findings list, not a task list. If you are an AI assistant reading this file:
> do not fix, refactor, or "clean up" any item below on your own initiative — ask first,
> even if the fix looks small or obvious. Feel free to remind whoever you're working with
> of this rule if they ask you to act on something here without having said so explicitly.

Compiled by cross-verifying `Project civion/auditor.py` and `Project civion/database.py`
(the `IS456_MASTER` dict, which is this project's ground-truth encoding of IS 456 — see
`PROJECT_OVERVIEW.md`) against real IS 456 requirements, by hand-constructing inputs and
running `run_civion_audit()` directly to see actual output. Only issues actually
demonstrated or directly read from the code are listed — nothing here is guessed.

## Confirmed live (reproduced by running `run_civion_audit()` directly)

### 1. `concrete_type` must match an exact string, or the cascade silently uses wrong generic defaults
`auditor.py` looks up `IS456_MASTER["TABLE_5_DURABILITY"][c_type]` — the dict only has the
exact keys `"Plain Concrete"` / `"Reinforced Concrete"`. Any other value (e.g. the very
plausible abbreviation `"RCC"`, different casing, extra whitespace) falls through to the
hardcoded fallback (`req_min_grade="M20"`, `req_min_cement=300`, `req_max_wc=0.55` at
`auditor.py` ~lines 81–84) instead of raising a warning that the concrete type couldn't be
matched. Reproduced: `concrete_type="RCC"`, `exposure="Severe"`, `specified_min_cement=300`,
`specified_wc=0.50` — real RCC/Severe minimums are 320 kg/m³ / 0.45 max w/c (should Fail),
but the engine reports both as Pass because it silently used the Mild-ish generic fallback
numbers instead of the Severe/RCC row.

Status (2026-10-28): STILL OPEN - re-ran the issue's input (`concrete_type="RCC"`, Severe, min cement 300, w/c 0.50): both rows still Pass against the fallback Min 300 / Max 0.55 (`resolve_limit` in `auditor.py` returns the `default` from `database.PARAMETERS`); the exact string "Reinforced Concrete" gives Min 320 / Max 0.45 and Fail.

### 2. Missing `cement_type` / `exposure` reported as a false Pass ("Must be defined")
`cem_type = get_val('cement_type', 'OPC')` and `exposure = get_val('exposure', 'Moderate')`
supply a default value, then the code checks `if c_type is not None: Pass`. Since the
default is never `None`, this check can never actually fail — it reports "Pass" even when
the field was never present in the extracted data at all. Reproduced by calling the audit
with `cement_type` and `exposure` entirely absent from the input: both show up as
`Pass — Must be defined` with the silently-substituted default value shown as if it were
extracted. (`fire_resistance_rating` avoids this same trap correctly, by using two separate
`get_val` calls — one with a default for calculations, one without a default for the
"is it actually present" check — `cement_type`/`exposure` don't follow that pattern.)

Status (2026-10-28): STILL OPEN - with `cement_type` and `exposure` absent, `run_civion_audit` (`auditor.py` lines 309-310) still substitutes "OPC" / "Moderate" and the ledger shows both as Pass "Must be defined".

### 3. Sulfate Class 2 requirement is internally wrong
Real IS 456 Table 4, Class 2 sulfate exposure gives two valid options: OPC/PSC/PPC at
330 kg/m³ minimum cement, or Super-Sulphate-Resisting cement at 310 kg/m³. `database.py`'s
`SULPHATE_ATTACK_EXPOSURE.classes["Class 2"]` collapses this into one wrong composite:
`min_cement: 310`, `cement_type: "SRC/PPC/PSC"`. Two consequences, both reproduced:
- A design using OPC at 315 kg/m³ (Class 2 exposure) reports **Pass** on "Min Cement
  Content" against a threshold of 310, when the real minimum for OPC is 330 (should Fail).
- The same design reports a **Warning** on "Sulfate Cement Type" (`"OPC" in "SRC/PPC/PSC"`
  evaluates `False`), even though OPC is explicitly permitted for Class 2 by the real table.

Note: `cement_type` in `SULPHATE_ATTACK_EXPOSURE.classes[...]` is a plain string checked with
Python's substring `in` operator rather than list membership — beyond the OPC exclusion bug
above, this is fragile in general (any 2+ letter cement code that happens to be a substring
of the allowed string would spuriously match).

Status (2026-10-28): STILL OPEN - `database.py` still has Class 2 as `min_cement` 310 with `cement_type` "SRC/PPC/PSC"; a re-run with soil SO3 0.3 %, OPC, 315 kg/m3 still gives Pass on Min Cement Content (limit 310) and Warning on Sulfate Cement Type (`audit_sulphate_cement` still uses substring `in`).

## Found by code reading (not yet reproduced live, high confidence)

### 4. Characteristic-strength acceptance check has a fabricated upper bound
`auditor.py` treats acceptance as `fck − 0.825·σ ≤ result ≤ fck + 0.825·σ`. Real IS 456
Cl. 16 / Table 11 has no upper cap — concrete stronger than the specified grade is never
non-compliant. As implemented, unusually strong concrete can be marked Fail/Warning. The
lower-bound formula also doesn't match the actual clause, which tests the *mean of a group
of 4 non-overlapping samples* against `fck + 0.825·s` (or `fck+3`, whichever is greater),
not a single "characteristic strength" value against `fck − k·σ`.

Status (2026-10-28): STILL OPEN - `audit_strength` in `auditor.py` still tests `fck - k*sigma <= strength <= fck + k*sigma` (comment: "kept unchanged"); M30, sigma 5, strength 45 N/mm2 gives Fail against 25.9 - 34.1.

### 5. Sampling-count formula off-by-one at exact 50 m³ multiples
`auditor.py`: `extra_samples = (extra_vol // 50) + 1`. For a volume exactly 50 m³ over the
base 50 (i.e. 100 m³ total), this should require 1 extra sample ("one additional per each
50 m³ or part thereof") but computes `50 // 50 + 1 = 2`. Should be a ceiling division. Minor
— makes the check stricter than required, not unsafe, but it is a real off-by-one.

Status (2026-10-28): FIXED - `is_samples()` in `auditor.py` now uses `math.ceil((volume - 50) / step)`; run: 100 m3 requires 5 sets (5 gives Pass), 101 m3 requires 6, and the "sampling count" cases in `test_dummy_audit.py` pass.

### 6. IS 383 cross-references are unconditionally marked Pass, no numeric check
Any `cross_references` entry the extractor produces (e.g. "aggregate grading deferred to
IS 383") is scored Pass regardless of whether the deferral is actually consistent with the
document's own text. `database.py` holds real reference numbers for this
(`EXTERNAL_CODE_REFERENCES`), but `auditor.py` never reads that dict — it's only used by
the chatbot side (`api/main.py`). So the cross-reference handling in the compliance check
is "trust the extractor," not a verified pass.

Status (2026-10-28): STILL OPEN - a reference is now a separate "Reference" status with its own count, but it is still counted in "pass" with no check against the document or IS 383, and `auditor.py` still does not import `EXTERNAL_CODE_REFERENCES` (only `api/main.py` does).

### 7. Several checks hardcode their IS 456 limit as a literal instead of reading `IS456_MASTER`
`database.py` defines dedicated config entries for these limits, but `auditor.py` hardcodes
the number directly in the `evaluate(...)` call instead of reading the dict entry that
exists for exactly this purpose. Values currently match, but the two copies can silently
drift apart since there's no single source of truth being enforced:
- Transportation Time: hardcoded `30`, vs. `CONSTRUCTION_PROCEDURES.Transportation.max_time_mins`
- Max Cement Content: hardcoded `450`, vs. `MATERIAL_PROPERTIES.Cement_Limits.max_content`
- Water pH: hardcoded `6.0`, vs. `MATERIAL_PROPERTIES.Water.min_ph`
- Sulphate (SO3) Content: hardcoded `4.0`, vs. `SULPHATE_LIMITS.max_water_soluble_so3_percent`
- Cube Size: hardcoded `150`, vs. `MATERIAL_PROPERTIES.Sampling_Standard.cube_size_mm`

Status (2026-10-28): FIXED - max cement, water pH, SO3 and cube size are now read from `IS456_MASTER` through `limit_from` paths in `database.PARAMETERS` (no 450 / 6.0 / 4.0 / 150 literals remain in `auditor.py`; run: 460 Fail, pH 5.9 Fail, SO3 4.1 Fail, cube 100 Fail), and the transport-time 30 limit was removed (`shape: "defined"`, 45 mins gives Pass).

### 8. `WORKABILITY` table in `database.py` is defined but never used
`database.py` defines slump ranges per concrete-usage category (mass/lightly reinforced:
25–75mm, normal RCC: 50–100mm, pumped/heavily reinforced: 100–150mm), but `auditor.py`'s
actual Slump check just uses one flat 25–150mm range regardless of category — the
category-specific table is dead data.

Status (2026-10-28): STILL OPEN - slump still uses one flat range (`WORKABILITY.overall_slump_mm` = [25, 150]); the per-category `slump_min` / `slump_max` entries in `database.py` are still never read (slump 120 mm gives Pass for any category).

### 9. Member cover check always uses the Reinforced Concrete cover table
`durability_table = IS456_MASTER["TABLE_16_NOMINAL_COVER"]["Reinforced_Concrete"]["Standard"]`
is used unconditionally, regardless of the audited `concrete_type`. There's no Plain
Concrete alternative in the data, so a Plain Concrete project's member cover is currently
checked against the RCC cover table. May be intentional (no PCC-specific table was ever
added) rather than a bug — flagging so it's a deliberate decision rather than an oversight.

Status (2026-10-28): STILL OPEN - `audit_covers` in `auditor.py` (line 424) still uses `TABLE_16_NOMINAL_COVER["Reinforced_Concrete"]["Standard"]` for every concrete type; run: Plain Concrete, Severe, 40 mm covers are checked against Min 45 mm.

## Explicitly checked and found correct (for reference — not issues)
- Sampling-frequency thresholds (1/2/3/4 samples at ≤5/15/30/50 m³) match the standard IS 456
  Cl. 15.2.2 table.
- Formwork removal days (slabs 3, beam soffit 7, props under slabs 7/14 @ 4.5m span, props
  under beams/arches 14/21 @ 6m span) all read correctly from `IS456_MASTER`.
- Sulfate Class 1, 3, 4, 5 cement-content/type/w-c entries all check out against the real
  Table 4 (only Class 2, item #3 above, is wrong).
- Chloride content limits by concrete type (0.4 prestressed / 0.6 RCC / 3.0 PCC) match Table 7.
- Mixing time (2 min), compaction-method prohibition list, and curing-days-by-cement-type all
  correctly read from `IS456_MASTER` rather than being hardcoded.
