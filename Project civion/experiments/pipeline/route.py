"""STEP 3b (v2) - scope expansion + Stage B routing.

1. Scope: Stage A's picks (localize.py, outline-only call) plus two
   deterministic safety nets added after the v1 audit:
   - descendants of a picked section that has its own body text;
   - sections whose heading contains a scope cue word (generic words such
     as "curing", "cement", "aggregate"; see SCOPE_HEADING_CUES).
   Anything pulled in by mistake is filtered out by routing below.
2. Units: units.py splits in-scope sections into clauses/tables.
3. Routing: batched JSON calls. For each unit the model sees its heading
   path and a preview (text: first ~300 chars; table: caption + header +
   first rows), plus the cue words that occur only later in the unit, and
   returns the group ids it feeds (multi-tag, "when unsure tag more").
   Ids the model leaves out are asked again once; still missing -> tagged
   with ALL groups (unsure = more).

Outputs: scope.json, units.json, routing.json.
"""
import re
import time

from common import OUT_DIR, call_groq, est_tokens, read_json, write_json
from groups import GROUPS
from units import section_units, table_preview

SCOPE_HEADING_CUES = ["cement", "concrete grade", "grades of concrete", "durab", "water", "admixture",
                      "aggregate", "curing", "cure", "mass concrete", "mix", "batch", "placing", "laying",
                      "compaction", "slump", "joint", "cover", "sampl", "testing", "acceptance",
                      "quality control", "exposure", "sulphate", "sulfate", "hot weather",
                      "cold weather", "weather"]
PREVIEW_CHARS = 300
BATCH_PREVIEW_TOKENS = 2600   # EST tokens of unit previews per routing call

SYSTEM = "You route specification text units to extraction groups. Output STRICTLY valid JSON."

PROMPT = """Each UNIT below is a short preview of one clause or table from a concrete
specification (heading path + the start of its text). Decide which extraction
GROUPS each unit may feed, i.e. could contain a value, limit, table row or
code reference for one of that group's parameters.

GROUPS:
{groups}

Rules:
- Multi-tag is allowed and expected (one table can feed several groups).
- When unsure, tag MORE groups, not fewer. A preview is truncated: "later
  mentions" lists words that occur further on in the unit.
- Tag [] only for units clearly unrelated to every group (e.g. formwork,
  reinforcement bar details, finishes, admin/submittals, plain lists of
  referenced standards).
- Return EVERY unit id exactly once.

Return JSON: {{"U-id": ["group", ...], ...}}  (use the unit ids exactly as given)

UNITS:
{units}"""


def heading_has_cue(heading):
    h = heading.lower()
    return any(re.search(r"\b" + re.escape(c), h) for c in SCOPE_HEADING_CUES)


def expand_scope(sections, selected):
    picked = {it["id"] for it in selected["selected"]}
    reasons = {sid: "stage_a" for sid in picked}
    by_id = {s["id"]: s for s in sections}
    for s in sections:
        if s["id"] in picked or not s["text"].strip():
            continue
        path = tuple(s["heading_path"])
        for anc in sections:
            ap = tuple(anc["heading_path"])
            if (anc["id"] in picked and reasons.get(anc["id"]) == "stage_a" and anc["text"].strip()
                    and len(ap) < len(path) and path[:len(ap)] == ap):
                reasons[s["id"]] = f"descendant_of:{anc['id']}"
                break
        else:
            if heading_has_cue(s["heading"]):
                reasons[s["id"]] = "heading_cue"
    scope = [sid for sid in by_id if sid in reasons]   # document order
    return scope, reasons


def cue_hints(text):
    later = text[PREVIEW_CHARS:].lower()
    first = text[:PREVIEW_CHARS].lower()
    hits = []
    for g in GROUPS.values():
        for p in g.params:
            for c in p.cues:
                c = c.lower()
                if c in later and c not in first and c not in hits:
                    hits.append(c)
    return hits[:12]


def preview(u):
    path = " > ".join(h if len(h) <= 80 else h[:77] + "..." for h in u["heading_path"][-2:])
    if u["kind"] == "table":
        body = table_preview(u["text"])
    else:
        body = u["text"][:PREVIEW_CHARS] + ("..." if len(u["text"]) > PREVIEW_CHARS else "")
    hints = cue_hints(u["text"]) if u["kind"] == "text" else []
    s = f"[{u['id']}] {path}\n{body}"
    if hints:
        s += f"\n(later mentions: {', '.join(hints)})"
    return s


def groups_text():
    return "\n".join(f"- {gid}: {g.routing_desc}. Parameters: {', '.join(p.name for p in g.params)}"
                     for gid, g in GROUPS.items())


def route_batch(name, units):
    prompt = PROMPT.format(groups=groups_text(), units="\n\n".join(preview(u) for u in units))
    res, call = call_groq(name, SYSTEM, prompt, expected_completion=1200, reasoning_effort="low")
    out = {}
    for k, v in (res or {}).items():
        if isinstance(v, list):
            out[str(k).strip().strip("[]")] = [g for g in v if g in GROUPS]
    return out, call


def main(out_dir=OUT_DIR):
    t0 = time.perf_counter()
    sections = read_json(out_dir / "sections.json")
    selected = read_json(out_dir / "selected.json")
    scope, reasons = expand_scope(sections, selected)
    sec_by_id = {s["id"]: s for s in sections}

    units = []
    for sid in scope:
        units += section_units(sec_by_id[sid])
    # Stage A may also pick a table id whose section is out of scope.
    for it in selected["selected"]:
        if it["kind"] == "table" and it["id"].split(".")[0] not in reasons:
            sec = sec_by_id[it["id"].split(".")[0]]
            t = next(t for t in sec["tables"] if t["id"] == it["id"])
            units.append({"id": f"{t['id']}.U1", "section_id": sec["id"], "kind": "table", "table_id": t["id"],
                          "heading_path": sec["heading_path"] + [f"[TABLE] {t['caption']}"],
                          "caption": t["caption"], "text": t["text"]})
    write_json(out_dir / "scope.json", {"scope": scope, "reasons": reasons})
    write_json(out_dir / "units.json", units)

    batches, cur, cur_tok = [], [], 0
    for u in units:
        tok = est_tokens(preview(u))
        if cur and cur_tok + tok > BATCH_PREVIEW_TOKENS:
            batches.append(cur)
            cur, cur_tok = [], 0
        cur.append(u)
        cur_tok += tok
    if cur:
        batches.append(cur)

    routing, calls = {}, []
    for n, b in enumerate(batches):
        res, call = route_batch(f"route[{n}]", b)
        call["n_units"] = len(b)
        calls.append(call)
        for u in b:
            if u["id"] in res:
                routing[u["id"]] = res[u["id"]]
    missing = [u for u in units if u["id"] not in routing]
    retried, defaulted = [u["id"] for u in missing], []
    if missing:
        res, call = route_batch("route[retry]", missing)
        call["n_units"] = len(missing)
        calls.append(call)
        for u in missing:
            if u["id"] in res:
                routing[u["id"]] = res[u["id"]]
            else:
                routing[u["id"]] = list(GROUPS)
                defaulted.append(u["id"])

    per_group = {g: {"units": 0, "chars": 0, "est_tokens": 0} for g in GROUPS}
    for u in units:
        for g in routing[u["id"]]:
            per_group[g]["units"] += 1
            per_group[g]["chars"] += len(u["text"])
            per_group[g]["est_tokens"] += est_tokens(u["text"])
    unrouted = [u["id"] for u in units if not routing[u["id"]]]
    write_json(out_dir / "routing.json", {
        "routing": {u["id"]: routing[u["id"]] for u in units},
        "per_group": per_group, "unrouted_units": unrouted,
        "retried_units": retried, "defaulted_to_all_groups": defaulted, "calls": calls})
    print(f"[route] scope {len(scope)} sections ({sum(1 for r in reasons.values() if r != 'stage_a')} added "
          f"by safety nets) -> {len(units)} units in {len(batches)} batches; "
          f"{len(unrouted)} routed to no group; retried {len(retried)}, defaulted {len(defaulted)}")
    for g, v in per_group.items():
        print(f"  {g}: {v['units']} units, ~{v['est_tokens']} tok (EST)")
    return {"wall_s": round(time.perf_counter() - t0, 2), "calls": calls, "n_units": len(units),
            "n_scope_sections": len(scope), "scope_reasons": reasons, "per_group": per_group,
            "unrouted": len(unrouted), "retried": retried, "defaulted": defaulted}
