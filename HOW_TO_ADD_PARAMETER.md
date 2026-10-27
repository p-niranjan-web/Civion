# How to add a parameter (or an IS code) to Civion

Written for whoever (person or AI) extends the audit later. All paths are inside `Project civion/`.

How it fits together: an LLM extracts values + verbatim quotes into JSON (field names = parameter
names) -> `auditor.py` compares each value with the IS ground truth in `database.py` -> the UI shows
Pass / Fail / Warning (missing) / Reference. `auditor.py` has one check per **shape**; a parameter only
declares its shape, so a new parameter normally needs **no new code**.

## Shapes (database.SHAPES)

| shape | value the extraction returns | passes when |
|---|---|---|
| `defined` | anything | it is stated (IS gives no number) |
| `min` | number, or `[low, high]` | value (low end of a range) >= limit |
| `max` | number, or `[low, high]` | value (high end of a range) <= limit |
| `range` | number, or `[low, high]` | the whole stated range lies in `[low, high]` |
| `equals` | number | value == limit |
| `not_in` | text | contains none of the prohibited words |
| `set_max` | `{group: {item: number}}` | every item the IS table also has is <= IS |
| `set_range` | `{group: {item: [low, high]}}` | every stated range lies inside the IS range |
| `sampling` | `[{from_m3, to_m3, samples, extra_per_m3}]` | every band asks for >= the IS number |

Single-use rules (`cover`, `strength_window`, `sampling_count`, `sulphate_cement`) exist for four
parameters whose logic is too specific; avoid adding more.

Any shape becomes **Reference** when the value is missing and `cross_references` has an entry with
`"parameter": "<field name>"` (the document says "as per IS xxx" / "as shown on the drawings").

## Steps to add a parameter

1. **Ground truth** - put the IS values in `database.py`, in the table of that code
   (`IS456_MASTER` or `IS383_2016`), with a `"clause"` entry. Values must come from the IS code
   text, never from a sample spec. If unsure, ask the repo owner.
2. **Parameter entry** - add one entry to `PARAMETERS` in `database.py` (order = ledger order):
   ```python
   "water_cube_strength_percent": {"metric": "Water - Cube Strength", "shape": "min", "unit": "%",
                                   "clause": "IS 456:2000 Clause 5.4.1.2", "limit": 90},
   ```
   Use `"limit_from": ["IS456", "TABLE_NAME", "{concrete_type}", "{exposure}", "column"]` instead of
   `"limit"` when the limit depends on the user's exposure / concrete type / cement type; add
   `"default"` for when the lookup finds nothing. Optional `"requirement"` text for `defined`.
3. **Extraction schema** - add the same field name to the JSON structure in `parser.py`
   (`prompt_all`, between "Return exactly this JSON structure" and `"cross_references"`).
4. **Pipeline group** - add one `P(name, type, rule, cues)` line to exactly one group in
   `experiments/pipeline/groups.py`. The rule says how to read it from any spec (no wording from one
   document). If a group's answers are large tables, give it a budget in `GROUP_BUDGETS`
   (`extract_v2.py`).
5. **Test** - add a pass, a fail and a missing case to `CASES` in `test_dummy_audit.py`, then run
   `python test_dummy_audit.py`. The last line must say all checks are as expected; the
   "schema sync" check fails if steps 2-4 use different names.
6. **Try it on a document** - `python experiments/pipeline/run_v2.py --run-name <name>` (Groq free
   tier: the runner paces itself to ~7,000 tokens/minute; a full run takes 10-20 minutes), then check
   `output_v2/<name>/quote_check.json`: do not claim a parameter works until it was extracted with a
   verbatim quote.

For a table parameter (`set_max` / `set_range`), the group and item names the LLM must use are read
from the IS table in `database.py` (`prompt_rules.table_keys_hint()`); add a line there for the new
field so the prompt lists its names.

## Steps to add an IS code

1. Add a dict for it in `database.py` (like `IS383_2016`), one key per table, each with `"clause"`.
2. Register its name in `resolve_limit()` in `auditor.py`:
   `{"IS456": is456_rules, "IS383": IS383_2016, "IS1234": IS1234_YEAR}` (the only code change).
3. Add parameters as above, using `"limit_from": ["IS1234", ...]`.

## Things not to do

- Do not copy a value from a sample specification into `database.py`.
- Do not shape a rule or prompt around one document's wording, numbering or table numbers.
- Do not edit the formwork entries (out of scope) or `JOURNEY.md` (maintained by the owner).
- Never print the Groq API key.
