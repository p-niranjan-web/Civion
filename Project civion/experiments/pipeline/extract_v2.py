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
the references rule is imported from parser.py; the per-field rules come from groups.py.
"""
import json
import time

from common import OUT_DIR, PROJECT_ROOT, call_groq, est_tokens, read_json, write_json
from groups import ALL_PARAMS, GROUPS
from parser import REFERENCES_RULE

FORMWORK_FIELDS = ["formwork_removal_hours", "formwork_removal_days", "formwork_span_m"]
SITE_FIELDS = ["soil_total_so3_percent", "soil_extract_2_1_so3_gl", "groundwater_so3_gl"]
MEMBERS = ["Beams", "Columns", "Slabs"]

SYSTEM = "You are a civil engineering parser. Output STRICTLY valid JSON. Do NOT invent values. If missing, return null."


def build_prompt(group_id, units_text, exposure, concrete_type):
    g = GROUPS[group_id]
    fields = "\n".join(f'      "{p.name}": {p.type},   // {p.rule}' for p in g.params)
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
    row label - not just the number.{notes}
    {REFERENCES_RULE}
    Return exactly:
    {{
{fields}
      "cross_references": [ {{ "parameter": "field name from above, or a short snake_case name", "points_to": "IS code like 'IS 383', or 'drawings' / other source", "source_quote": "exact quote" }} ],
      "source_quotes": {{ "<field>": "verbatim quote for every non-null field" }}
    }}
    EXCERPTS:
{units_text}
    """


def unit_block(u):
    return f"### [{u['id']}] {' > '.join(u['heading_path'])}\n{u['text']}"


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
    return v is None or v == "" or v == [] or v == {}


def merge_group(group_id, results):
    """results: [(batch_idx, parsed)] -> (values, quotes, conflicts, xrefs)."""
    values, quotes, conflicts = {}, {}, []
    for p in GROUPS[group_id].params:
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
    return values, quotes, conflicts, xrefs


def fallback_hook(extraction, out_dir):
    """Unchanged from v1: list null params if the keyword file exists.
    The keyword fallback search itself is NOT implemented."""
    kw = PROJECT_ROOT / "experiments" / "fallback_search" / "keywords.json"
    nulls = [f for f in ALL_PARAMS if f != "member_covers" and extraction.get(f) is None]
    nulls += [f"member_covers.{m}" for m in MEMBERS if not (extraction.get("member_covers") or {}).get(m)]
    if kw.exists():
        write_json(out_dir / "fallback_candidates.json", {"keywords_file": str(kw), "null_params": nulls})
    return {"keywords_found": kw.exists(), "null_params": nulls}


def main(out_dir=OUT_DIR, exposure="Moderate", concrete_type="Reinforced Concrete",
         max_call_tokens=5000, completion_reserve=1200):
    t0 = time.perf_counter()
    units = read_json(out_dir / "units.json")
    routing = read_json(out_dir / "routing.json")["routing"]
    calls, extraction, conflicts, xrefs = [], {}, [], []
    quotes = {}
    (out_dir / "extract_calls").mkdir(exist_ok=True)
    for gid in GROUPS:
        g_units = [u for u in units if gid in routing.get(u["id"], [])]
        if not g_units:
            for p in GROUPS[gid].params:
                extraction[p.name] = None
            print(f"[extract_v2] {gid}: no units routed - all fields null")
            continue
        template = est_tokens(SYSTEM + build_prompt(gid, "", exposure, concrete_type))
        budget = max_call_tokens - template - completion_reserve
        batches = make_batches(g_units, budget)
        results = []
        for b, text in enumerate(batches):
            parsed, call = call_groq(f"extract[{gid}#{b}]", SYSTEM, build_prompt(gid, text, exposure, concrete_type),
                                     expected_completion=completion_reserve)
            call.update(group=gid, batch=b, text_chars=len(text))
            calls.append(call)
            results.append((b, parsed or {}))
            write_json(out_dir / "extract_calls" / f"{gid}_{b}.json",
                       {"group": gid, "batch": b, "text": text, "response": parsed, "call": call})
        values, q, c, x = merge_group(gid, results)
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
    hook = fallback_hook(extraction, out_dir)
    return extraction, {"wall_s": round(time.perf_counter() - t0, 2), "calls": calls, "fallback_hook": hook}
