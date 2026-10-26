"""STEP 4 - extract the parser.py JSON schema from the localized text only.

The prompt (schema + rules + exposure / concrete-type context) is copied from
parser.py's single-pass prompt, minus the three formwork fields, which are
skipped and returned as null. Instead of clean_text[:12000], the localized
items are packed per topic group (as tagged by localize.py) into chunks so
each call stays under --max-call-tokens total (prompt + completion,
ESTIMATED as chars/4 before the call; the MEASURED usage is recorded).

Merge: for each field, the value from a call of the group that "owns" the
field wins (first in document order); otherwise the first non-null value from
any call. Every non-null candidate is kept in extraction["_candidates"] so
conflicts are visible.

Usage: python extract.py [--exposure Moderate] [--concrete-type "Reinforced Concrete"]
"""
import argparse
import time

from common import OUT_DIR, PROJECT_ROOT, call_groq, est_tokens, read_json, write_json

FORMWORK_FIELDS = ["formwork_removal_hours", "formwork_removal_days", "formwork_span_m"]

# Which topic group's text is the natural home of each field (merge priority).
FIELD_OWNER = {
    "materials": ["cement_type", "water_ph", "water_organic_mg_l", "water_inorganic_mg_l",
                  "water_sulphates_mg_l", "water_chlorides_mg_l", "water_suspended_matter_mg_l",
                  "measured_chloride_content", "measured_so3_percent"],
    "durability_grade": ["exposure", "freezing_thawing_exposure", "soil_total_so3_percent",
                         "soil_extract_2_1_so3_gl", "groundwater_so3_gl", "concrete_type",
                         "specified_grade", "specified_min_cement", "specified_max_cement",
                         "specified_wc", "specified_characteristic_strength", "specified_sigma"],
    "production_curing": ["mixing_time_minutes", "transport_time_minutes", "compaction_method",
                          "curing_days", "specified_slump_mm"],
    "cover_sampling": ["total_volume_m3", "specified_sampling_sets", "sampling_cube_size_mm",
                       "fire_resistance_rating", "member_covers"],
}
OWNER_OF = {f: g for g, fs in FIELD_OWNER.items() for f in fs}
SCALAR_FIELDS = [f for fs in FIELD_OWNER.values() for f in fs if f != "member_covers"]

SYSTEM_INSTRUCTION = "You are a civil engineering parser. Output STRICTLY valid JSON. Do NOT invent values. If missing, return null."


def build_prompt(text_chunk, detected_exposure, detected_concrete_type):
    """parser.py's prompt, verbatim except: formwork keys removed from the
    schema and a one-line note that the text is an excerpt."""
    exposure_context = ""
    if detected_exposure:
        exposure_context = (
            f"\n    IMPORTANT CONTEXT: The applicable environmental exposure condition for this "
            f"structure has ALREADY been determined externally to be \"{detected_exposure}\". "
            f"The document may describe specifications for a single exposure condition, or it may "
            f"list several different exposure cases/scenarios. If more than one exposure case is "
            f"present, extract ONLY the values that apply to the \"{detected_exposure}\" exposure "
            f"case and ignore the values given for the other exposure cases. Always set the "
            f"\"exposure\" field to \"{detected_exposure}\".\n"
            f"    TABLE RESOLUTION: Some documents do not state a single number but instead give a "
            f"REQUIREMENTS TABLE whose rows are exposure classes (Mild / Moderate / Severe / Very "
            f"Severe / Extreme) and whose columns are the concrete type (Plain Concrete vs "
            f"Reinforced Concrete) and/or the parameter (minimum cement content, maximum "
            f"water-cement ratio, minimum grade, nominal cover, sampling frequency, etc.). "
            f"When a value is only available from such a table, you MUST look it up: pick the row "
            f"for the \"{detected_exposure}\" exposure class"
            + (f" and the \"{detected_concrete_type}\" column" if detected_concrete_type else " and the applicable concrete-type column")
            + f", then return that cell's number as the field value. Do NOT leave the field null "
            f"when the number can be read from a table row - resolve it. Put the exact table "
            f"row/cell text in source_quotes.\n"
        )
    if detected_concrete_type:
        concrete_type_hint = (
            f' The applicable concrete type for this structure is "{detected_concrete_type}" - '
            f'set "concrete_type" to that and read every exposure/concrete-type table using that column.'
        )
    else:
        concrete_type_hint = (
            ' If the document names both plain and reinforced concrete, choose the one it says is '
            'used for the actual structural members (e.g. "reinforced cement concrete shall be used '
            'typically at all locations" => "Reinforced Concrete").'
        )
    return f"""
    Extract the concrete specification below into ONE JSON object.
    Rules: use only values stated (or table-resolvable) in the text; if a value
    is missing return null; never invent numbers.
    The text is an EXCERPT (selected sections) of a longer document; fields not
    covered by this excerpt must be null.
    For "concrete_type" return exactly "Plain Concrete" or "Reinforced Concrete" as a single string.{concrete_type_hint}
    The "water_organic_mg_l", "water_inorganic_mg_l", "water_sulphates_mg_l",
    "water_chlorides_mg_l" and "water_suspended_matter_mg_l" fields come from a
    "PERMISSIBLE LIMITS FOR SOLIDS (IN WATER)" style table (mixing/curing water
    quality per IS 456 Table 1) - do NOT confuse this with the soil/groundwater
    sulphate-attack fields above (soil_total_so3_percent, soil_extract_2_1_so3_gl,
    groundwater_so3_gl), which come from a different table.
    {exposure_context}
    Return exactly this JSON structure (same keys, correct types):
    {{
      "exposure": "Mild|Moderate|Severe|Very Severe|Extreme",
      "freezing_thawing_exposure": bool,
      "water_ph": float,
      "soil_total_so3_percent": float,
      "soil_extract_2_1_so3_gl": float,
      "groundwater_so3_gl": float,
      "concrete_type": "Plain Concrete|Reinforced Concrete",
      "specified_grade": "string like M20",
      "cement_type": "OPC|PPC|PSC|SRC|Mineral Admixture",
      "specified_min_cement": int,
      "specified_max_cement": int,
      "specified_wc": float,
      "specified_characteristic_strength": int,
      "specified_sigma": int,
      "mixing_time_minutes": int,
      "transport_time_minutes": int,
      "compaction_method": "mechanical vibrator|manual|hand|ramming",
      "curing_days": int,
      "specified_slump_mm": int,
      "total_volume_m3": int,
      "specified_sampling_sets": int,
      "sampling_cube_size_mm": int,
      "measured_chloride_content": float,
      "measured_so3_percent": float,
      "fire_resistance_rating": "0.5hr|1hr|1.5hr|2hr|4hr",
      "member_covers": {{ "Beams": int, "Columns": int, "Slabs": int }},
      "water_organic_mg_l": float,
      "water_inorganic_mg_l": float,
      "water_sulphates_mg_l": float,
      "water_chlorides_mg_l": float,
      "water_suspended_matter_mg_l": float,
      "cross_references": [ {{ "parameter": "string - which requirement is being deferred, e.g. coarse_aggregate_grading", "referenced_code": "string like 'IS 383'", "source_quote": "exact quote from text" }} ],
      "source_quotes": {{ "<field>": "exact quote from text for every non-null field above" }}
    }}
    CROSS-REFERENCES: A spec may state a requirement not as a number but by
    deferring it to another IS code (e.g. "Grading of coarse aggregate shall
    conform to the requirements of IS 383."). This is NOT missing data - do
    NOT return null for it and do NOT treat it as a failure. Instead add one
    entry to "cross_references" per such statement, naming the parameter it
    concerns, the exact code referenced (e.g. "IS 383"), and the exact quote.
    If there are no such deferrals, return an empty list.
    Text: {text_chunk}
    """


def split_block(block, budget_chars):
    """Split one oversized block on line boundaries, keeping its header line."""
    header, _, body = block.partition("\n")
    parts, cur = [], []
    for line in body.splitlines():
        if cur and len("\n".join(cur)) + len(line) > budget_chars:
            parts.append(header + " (cont.)\n" + "\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        parts.append(header + ("\n" if not parts else " (cont.)\n") + "\n".join(cur))
    return parts


def make_chunks(items, text_budget_tokens):
    """Pack items (doc order) per group into chunks of <= text budget."""
    budget_chars = text_budget_tokens * 4
    chunks = []
    for grp in FIELD_OWNER:
        blocks = []
        for it in items:
            if it["group"] == grp and it["text"].strip():
                block = f"## {' > '.join(it['heading_path'])}\n{it['text']}"
                blocks += split_block(block, budget_chars) if len(block) > budget_chars else [block]
        cur = []
        for b in blocks:
            if cur and len("\n\n".join(cur + [b])) > budget_chars:
                chunks.append({"group": grp, "text": "\n\n".join(cur)})
                cur = []
            cur.append(b)
        if cur:
            chunks.append({"group": grp, "text": "\n\n".join(cur)})
    return chunks


def is_empty(v):
    return v is None or v == "" or v == [] or v == {}


def merge(results):
    """results: list of (group, chunk_index, parsed_json) in call order."""
    merged = {}
    quotes = {}
    candidates = {}
    for field in SCALAR_FIELDS:
        cands = [(g, i, r.get(field), (r.get("source_quotes") or {}).get(field))
                 for g, i, r in results if isinstance(r, dict) and not is_empty(r.get(field))]
        if cands:
            candidates[field] = [{"group": g, "chunk": i, "value": v, "quote": q} for g, i, v, q in cands]
            owned = [c for c in cands if c[0] == OWNER_OF[field]]
            g, i, v, q = (owned or cands)[0]
            merged[field] = v
            if q:
                quotes[field] = q
        else:
            merged[field] = None

    covers = {}
    for member in ["Beams", "Columns", "Slabs"]:
        cands = []
        for g, i, r in results:
            mc = r.get("member_covers") if isinstance(r, dict) else None
            if isinstance(mc, dict) and not is_empty(mc.get(member)):
                cands.append((g, i, mc[member], (r.get("source_quotes") or {}).get("member_covers")))
        if cands:
            candidates[f"member_covers.{member}"] = [{"group": g, "chunk": i, "value": v, "quote": q} for g, i, v, q in cands]
            owned = [c for c in cands if c[0] == OWNER_OF["member_covers"]]
            g, i, v, q = (owned or cands)[0]
            covers[member] = v
            if q and "member_covers" not in quotes:
                quotes["member_covers"] = q
    merged["member_covers"] = covers or None

    xrefs, seen = [], set()
    for _, _, r in results:
        for x in (r.get("cross_references") or []) if isinstance(r, dict) else []:
            if not isinstance(x, dict):
                continue
            key = (str(x.get("parameter", "")).lower(), str(x.get("referenced_code", "")).replace(" ", "").upper())
            if key not in seen:
                seen.add(key)
                xrefs.append(x)
    merged["cross_references"] = xrefs
    for f in FORMWORK_FIELDS:
        merged[f] = None  # skipped by design
    merged["source_quotes"] = quotes
    merged["_candidates"] = candidates
    return merged


def fallback_hook(merged):
    """If experiments/fallback_search/keywords.json exists, list null params.
    The fallback search itself is NOT implemented yet."""
    kw = PROJECT_ROOT / "experiments" / "fallback_search" / "keywords.json"
    nulls = [f for f in SCALAR_FIELDS if merged.get(f) is None]
    nulls += [f"member_covers.{m}" for m in ["Beams", "Columns", "Slabs"]
              if not (merged.get("member_covers") or {}).get(m)]
    if kw.exists():
        write_json(OUT_DIR / "fallback_candidates.json", {"keywords_file": str(kw), "null_params": nulls})
        print(f"[extract] fallback hook: keywords.json found; {len(nulls)} null params listed")
        return {"keywords_found": True, "null_params": nulls}
    print("[extract] fallback hook: experiments/fallback_search/keywords.json not found - skipped")
    return {"keywords_found": False, "null_params": nulls}


def main(exposure="Moderate", concrete_type="Reinforced Concrete", max_call_tokens=5000,
         completion_reserve=1500):
    t0 = time.perf_counter()
    sel = read_json(OUT_DIR / "selected.json")
    sections = {s["id"]: s for s in read_json(OUT_DIR / "sections.json")}
    tables = {t["id"]: t for s in sections.values() for t in s["tables"]}
    items = []
    for it in sel["selected"]:
        src = sections.get(it["id"]) or tables.get(it["id"])
        items.append({**it, "text": src["text"]})

    template_tokens = est_tokens(SYSTEM_INSTRUCTION + build_prompt("", exposure, concrete_type))
    text_budget = max_call_tokens - template_tokens - completion_reserve
    chunks = make_chunks(items, text_budget)
    print(f"[extract] template ~{template_tokens} tok (est), text budget ~{text_budget} tok/call, "
          f"{len(chunks)} calls")

    results, calls = [], []
    for n, ch in enumerate(chunks):
        prompt = build_prompt(ch["text"], exposure, concrete_type)
        parsed, call = call_groq(f"extract[{n}] {ch['group']}", SYSTEM_INSTRUCTION, prompt,
                                 expected_completion=completion_reserve)
        call["group"] = ch["group"]
        call["text_chars"] = len(ch["text"])
        calls.append(call)
        results.append((ch["group"], n, parsed or {}))
        (OUT_DIR / "extract_calls").mkdir(exist_ok=True)
        write_json(OUT_DIR / "extract_calls" / f"call_{n:02d}_{ch['group']}.json",
                   {"group": ch["group"], "text": ch["text"], "response": parsed, "call": call})

    merged = merge(results)
    # Stamp the externally determined context, as parser.py does.
    merged["exposure"] = exposure
    merged["source_quotes"].setdefault("exposure", f"Exposure condition determined outside the document: {exposure}")
    merged["concrete_type"] = concrete_type
    merged["source_quotes"].setdefault("concrete_type", f"Concrete type determined outside the document: {concrete_type}")

    hook = fallback_hook(merged)
    return merged, {"wall_s": round(time.perf_counter() - t0, 2), "calls": calls,
                    "template_tokens_est": template_tokens, "text_budget_tokens_est": text_budget,
                    "fallback_hook": hook}


def cli_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--exposure", default="Moderate")
    ap.add_argument("--concrete-type", default="Reinforced Concrete")
    ap.add_argument("--max-call-tokens", type=int, default=5000)
    return ap.parse_args(argv)


if __name__ == "__main__":
    a = cli_args()
    merged, info = main(a.exposure, a.concrete_type, a.max_call_tokens)
    write_json(OUT_DIR / "extraction.json", merged)
    write_json(OUT_DIR / "extract_info.json", info)
