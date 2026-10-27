"""STEP 4 (v2) - per-group extraction from routed units.

For each group in groups.py: one call with only that group's fields and
rules plus only the units routed to it (document order, heading paths). A
group whose units do not fit in --max-call-tokens is split into batches.

Merge within a group: non-null wins; when batches disagree, the first value
in document order is used AND every candidate goes to extraction["conflicts"]
(and the report), so the choice is never silent. Groups do not share fields,
so merging across groups is a union; cross_references are deduplicated.

The shared rules (no invented values, null if missing, exposure-table
resolution, concrete-type column) are copied from parser.py's prompt;
the references and table-quote rules come from prompt_rules.py; the per-field rules come from groups.py.
"""
import json
import re
import time

from common import OUT_DIR, PROJECT_ROOT, call_groq, est_tokens, read_json, write_json
from groups import ALL_PARAMS, GROUPS
from database import PARAMETERS
import table_reader
from prompt_rules import REFERENCES_RULE, REMARKS_RULE, TABLE_QUOTE_RULE

FORMWORK_FIELDS = ["formwork_removal_hours", "formwork_removal_days", "formwork_span_m"]
SITE_FIELDS = ["soil_total_so3_percent", "soil_extract_2_1_so3_gl", "groundwater_so3_gl"]
MEMBERS = ["Beams", "Columns", "Slabs"]

# Groups whose answers are large tables need a bigger completion budget:
# group -> (max tokens per call, completion reserve).
GROUP_BUDGETS = {"aggregates": (6000, 2500)}
# Groups extracted one field per call. Tried for "aggregates" on BLR: no gain
# (the 11-column coarse grading table was still misread), 4x the tokens.
SPLIT_BY_FIELD = set()
PARAM_NAMES = set(ALL_PARAMS) | {"member_covers"}
# {group: {item: value}} fields are merged cell by cell across batches.
TABLE_FIELDS = {f for f, s in PARAMETERS.items() if s["shape"] in ("set_max", "set_range")}
# Grading tables (sieve rows x designation columns): the model names the table
# and its columns, Python reads the cells (table_reader.py).
READ_BY_PYTHON = {f for f, s in PARAMETERS.items() if s["shape"] == "set_range"}

SYSTEM = "You are a civil engineering parser. Output STRICTLY valid JSON. Do NOT invent values. If missing, return null."


def build_prompt(group_id, units_text, exposure, concrete_type, only=None):
    g = GROUPS[group_id]
    params = [p for p in g.params if only is None or p.name == only]
    fields = "\n".join(f'      "{p.name}": {p.type},   // {p.rule}' for p in params)
    notes = "".join(f"\n    NOTE: {n}" for n in g.notes)
    return f"""
    Extract the "{g.title}" parameters of a concrete specification into ONE JSON object.
    Rules: use only values stated (or table-resolvable) in the text; if a value
    is missing return null; never invent numbers. The text is a set of EXCERPTS
    (clauses/tables selected for this topic), each headed by its location.
    CONTEXT: exposure condition (determined outside the document) = "{exposure}";
    concrete type = "{concrete_type}".
    TABLE RESOLUTION: when a value is only given in a requirements table keyed by
    exposure class (rows) and concrete type / parameter (columns), read the
    "{exposure}" row and the "{concrete_type}" column and return that cell.
    SOURCE QUOTES: for every non-null field, copy the supporting text VERBATIM
    from the excerpts - a whole sentence, or the whole table row including its
    row label - not just the number.
    {TABLE_QUOTE_RULE}{notes}
    {REFERENCES_RULE}
    {REMARKS_RULE}
    Return exactly:
    {{
{fields}
      "cross_references": [ {{ "parameter": "field name from above, or a short snake_case name", "points_to": "IS code like 'IS 383', or 'drawings' / other source", "source_quote": "exact quote" }} ],
      "source_quotes": {{ "<field>": "verbatim quote for every non-null field" }},
      "remarks": {{ "<field>": "one short sentence, only when ambiguous" }}
    }}
    EXCERPTS:
{units_text}
    """


def unit_block(u):
    # Docling pads table cells with runs of spaces; drop them to save tokens
    # (verify.py ignores pipe spacing, so quotes still match the document).
    lines = u["text"].splitlines()
    text = "\n".join(re.sub(r" {2,}", " ", line) if line.lstrip().startswith("|") else line for line in lines)
    return f"### [{u['id']}] {' > '.join(u['heading_path'])}\n{text}"


def make_batches(units, budget_tokens):
    batches, cur = [], []
    for u in units:
        blk = unit_block(u)
        if cur and est_tokens("\n\n".join(cur + [blk])) > budget_tokens:
            batches.append(cur)
            cur = []
        cur.append(blk)
    if cur:
        batches.append(cur)
    return ["\n\n".join(b) for b in batches]


def is_empty(v):
    # A table answer whose cells are all null ({"zone I": {"10 mm": null}}) is empty too.
    if isinstance(v, dict):
        return all(is_empty(x) for x in v.values())
    return v is None or v == "" or v == []


def merge_table(name, group_id, results):
    """Cell-by-cell union of a {group: {item: value}} field across batches; the
    first value in document order wins, disagreements are conflicts."""
    merged, conflicts, quote = {}, [], None
    for i, r in results:
        v = r.get(name)
        if not isinstance(v, dict):
            continue
        for g, items in v.items():
            for item, cell in (items.items() if isinstance(items, dict) else []):
                if is_empty(cell):
                    continue
                old = merged.setdefault(g, {}).get(item)
                if old is None:
                    merged[g][item] = cell
                elif json.dumps(old) != json.dumps(cell):
                    conflicts.append({"field": f"{name}.{g}.{item}", "group": group_id,
                                      "candidates": [{"batch": "first", "value": old}, {"batch": i, "value": cell}]})
        quote = quote or (r.get("source_quotes") or {}).get(name)
    return merged or None, quote, conflicts


def merge_group(group_id, results):
    """results: [(batch_idx, parsed)] -> (values, quotes, conflicts, xrefs, remarks)."""
    values, quotes, conflicts = {}, {}, []
    for p in GROUPS[group_id].params:
        if p.name in TABLE_FIELDS:
            values[p.name], q, c = merge_table(p.name, group_id, results)
            if q and values[p.name]:
                quotes[p.name] = q
            conflicts += c
            continue
        if p.name == "member_covers":
            covers = {}
            for m in MEMBERS:
                cands = [(i, r["member_covers"][m]) for i, r in results
                         if isinstance(r.get("member_covers"), dict) and not is_empty(r["member_covers"].get(m))]
                if cands:
                    covers[m] = cands[0][1]
                    if len({json.dumps(v) for _, v in cands}) > 1:
                        conflicts.append({"field": f"member_covers.{m}", "group": group_id,
                                          "candidates": [{"batch": i, "value": v} for i, v in cands]})
            values["member_covers"] = covers or None
            q = next(((r.get("source_quotes") or {}).get("member_covers") for i, r in results
                      if (r.get("source_quotes") or {}).get("member_covers")), None)
            if q and covers:
                quotes["member_covers"] = q
            continue
        cands = [(i, r.get(p.name), (r.get("source_quotes") or {}).get(p.name))
                 for i, r in results if not is_empty(r.get(p.name))]
        if not cands:
            values[p.name] = None
            continue
        values[p.name] = cands[0][1]
        if cands[0][2]:
            quotes[p.name] = cands[0][2]
        if len({json.dumps(v) for _, v, _ in cands}) > 1:
            conflicts.append({"field": p.name, "group": group_id, "chosen": cands[0][1],
                              "candidates": [{"batch": i, "value": v, "quote": q} for i, v, q in cands]})
    xrefs = [x for _, r in results for x in (r.get("cross_references") or []) if isinstance(x, dict)]
    # Remarks: the model's own (first one per field), plus one per conflict so
    # the user sees that the document states more than one value.
    remarks = {}
    for _, r in results:
        model_remarks = r.get("remarks") if isinstance(r.get("remarks"), dict) else {}
        for f, text in model_remarks.items():
            if f in PARAM_NAMES and text and f not in remarks:
                remarks[f] = str(text)
    for c in conflicts:
        f = c["field"].split(".")[0] if c["field"].split(".")[0] in TABLE_FIELDS else c["field"]
        vals = ", ".join(json.dumps(x["value"], ensure_ascii=False) for x in c["candidates"])
        note = f"The document states different values ({vals}); the first in document order is audited."
        remarks[f] = f"{remarks[f]} {note}" if f in remarks else note
    return values, quotes, conflicts, xrefs, remarks


def fallback_hook(extraction, out_dir):
    """Unchanged from v1: list null params if the keyword file exists.
    The keyword fallback search itself is NOT implemented."""
    kw = PROJECT_ROOT / "experiments" / "fallback_search" / "keywords.json"
    nulls = [f for f in ALL_PARAMS if f != "member_covers" and extraction.get(f) is None]
    nulls += [f"member_covers.{m}" for m in MEMBERS if not (extraction.get("member_covers") or {}).get(m)]
    if kw.exists():
        write_json(out_dir / "fallback_candidates.json", {"keywords_file": str(kw), "null_params": nulls})
    return {"keywords_found": kw.exists(), "null_params": nulls}


def read_tables(parsed, units_by_id):
    """Replace a {"table", "columns"} answer for a READ_BY_PYTHON field by the
    cells read from the document (table_reader.py); the quote is set from the
    table's own lines. A failed read becomes null with a remark."""
    for f in READ_BY_PYTHON:
        answer = parsed.get(f)
        if not (isinstance(answer, dict) and "columns" in answer):
            continue
        cells, quote_or_problem = table_reader.read_table(answer, units_by_id)
        parsed[f] = cells
        if cells:
            parsed.setdefault("source_quotes", {})[f] = quote_or_problem
        else:
            parsed.setdefault("remarks", {})[f] = f"Table could not be read: {quote_or_problem}"


def extract_group(gid, g_units, out_dir, exposure, concrete_type, max_call_tokens=5000, completion_reserve=1200):
    """All calls of one group -> ([(batch_key, parsed)], [call logs]). Groups in
    SPLIT_BY_FIELD get one pass per field; their results merge like batches."""
    call_max, reserve = GROUP_BUDGETS.get(gid, (max_call_tokens, completion_reserve))
    passes = [p.name for p in GROUPS[gid].params] if gid in SPLIT_BY_FIELD else [None]
    results, calls = [], []
    for only in passes:
        template = est_tokens(SYSTEM + build_prompt(gid, "", exposure, concrete_type, only))
        batches = make_batches(g_units, call_max - template - reserve)
        for b, text in enumerate(batches):
            key = f"{gid}{'.' + only if only else ''}#{b}"
            parsed, call = call_groq(f"extract[{key}]", SYSTEM,
                                     build_prompt(gid, text, exposure, concrete_type, only),
                                     expected_completion=reserve)
            call.update(group=gid, field=only, batch=b, text_chars=len(text))
            calls.append(call)
            if parsed:
                read_tables(parsed, {u["id"]: u for u in g_units})
            results.append((len(results), parsed or {}))
            write_json(out_dir / "extract_calls" / f"{key.replace('#', '_')}.json",
                       {"group": gid, "field": only, "batch": b, "text": text, "response": parsed, "call": call})
    return results, calls


def main(out_dir=OUT_DIR, exposure="Moderate", concrete_type="Reinforced Concrete",
         max_call_tokens=5000, completion_reserve=1200):
    t0 = time.perf_counter()
    units = read_json(out_dir / "units.json")
    routing = read_json(out_dir / "routing.json")["routing"]
    calls, extraction, conflicts, xrefs = [], {}, [], []
    quotes, remarks = {}, {}
    (out_dir / "extract_calls").mkdir(exist_ok=True)
    for gid in GROUPS:
        g_units = [u for u in units if gid in routing.get(u["id"], [])]
        if not g_units:
            for p in GROUPS[gid].params:
                extraction[p.name] = None
            print(f"[extract_v2] {gid}: no units routed - all fields null")
            continue
        results, g_calls = extract_group(gid, g_units, out_dir, exposure, concrete_type,
                                         max_call_tokens, completion_reserve)
        calls += g_calls
        values, q, c, x, rm = merge_group(gid, results)
        remarks.update(rm)
        extraction.update(values)
        quotes.update(q)
        conflicts += c
        xrefs += x

    seen, dedup = set(), []
    for x in xrefs:
        key = (str(x.get("parameter", "")).lower(), str(x.get("points_to") or x.get("referenced_code") or "").replace(" ", "").upper())
        if key not in seen:
            seen.add(key)
            dedup.append(x)
    for f in FORMWORK_FIELDS + SITE_FIELDS:
        extraction[f] = None
    # Stamp externally supplied context. v1 bug: setdefault kept a model-written
    # quote for concrete_type that is not in the document - always overwrite.
    extraction["exposure"] = exposure
    extraction["concrete_type"] = concrete_type
    quotes["exposure"] = f"Exposure condition determined outside the document: {exposure}"
    quotes["concrete_type"] = f"Concrete type determined outside the document: {concrete_type}"
    extraction["cross_references"] = dedup
    extraction["source_quotes"] = quotes
    extraction["conflicts"] = conflicts
    extraction["remarks"] = remarks
    hook = fallback_hook(extraction, out_dir)
    return extraction, {"wall_s": round(time.perf_counter() - t0, 2), "calls": calls, "fallback_hook": hook}
