"""v4 runner: Docling markdown -> ONE Gemini call on the whole document ->
contract JSON -> Python quote check -> auditor.run_civion_audit (unchanged).

No section picking, routing or batching. The document is cleaned exactly like
v2 (experiments/pipeline/clean.py: image markers, entities, repeated page
headers) and Docling's table padding is squeezed; the quote check runs on that
same text (verify.py ignores pipe spacing).

Every run writes output/<run-name>/: doc.md (text sent), response.json (raw
model answer), extraction.json (contract + field_info), audit.json,
quote_check.json, location_check.json, run_stats.json.

Usage (conda env civion):
  python run_v4.py --run-name lite1 --role lite
  python run_v4.py --run-name main1 --role main          # counts against the 20/day budget
  python run_v4.py --run-name lite1b --from-raw lite1    # re-post-process a saved answer, no call
Options: --exposure Moderate --concrete-type "Reinforced Concrete" --tables python|model --input <docling.md>
"""
import argparse
import json
import re
import time
from pathlib import Path

import gemini_call
from gemini_call import HERE, call_gemini, model_id, remaining_today, used_today, limits_for
import prompt_v4
from prompt_v4 import FIELDS, GRADING_FIELDS, TYPES
import tables_v4

DEFAULT_IN = gemini_call.PROJECT_ROOT / "experiments" / "parse_test" / "docling_output.md"
OUT = HERE / "output"
FORMWORK_FIELDS = ["formwork_removal_hours", "formwork_removal_days", "formwork_span_m"]
MEMBERS = ["Beams", "Columns", "Slabs"]


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def prepare_doc(src):
    import clean as v2_clean          # experiments/pipeline/clean.py
    text, removed = v2_clean.clean(Path(src).read_text(encoding="utf-8"))
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            line = re.sub(r"-{3,}", "---", re.sub(r" {2,}", " ", line))
        lines.append(line)
    return "\n".join(lines) + "\n", {"input_chars": len(Path(src).read_text(encoding="utf-8")),
                                      "clean_chars": len(text), "sent_chars": len("\n".join(lines)),
                                      "repeated_lines_removed": sum(removed.values())}


def is_empty(v):
    if isinstance(v, dict):
        return all(is_empty(x) for x in v.values())
    return v is None or v == "" or v == []


def to_contract(parsed, doc, exposure, concrete_type, table_mode):
    """Model answer -> the existing extraction contract (+ field_info beside it)."""
    quotes_in = parsed.get("source_quotes") if isinstance(parsed.get("source_quotes"), dict) else {}
    remarks_in = parsed.get("remarks") if isinstance(parsed.get("remarks"), dict) else {}
    info_in = parsed.get("field_info") if isinstance(parsed.get("field_info"), dict) else {}
    ext, quotes, remarks, notes = {}, {}, {}, []
    for f in FIELDS:
        v = parsed.get(f)
        if f in GRADING_FIELDS and table_mode == "python" and isinstance(v, dict) and "columns" in v:
            cells, quote_or_problem = tables_v4.read_table(v, doc)
            if cells:
                v = cells
                quotes[f] = quote_or_problem
            else:
                v = None
                remarks[f] = f"Table could not be read: {quote_or_problem}"
                notes.append(f"{f}: {quote_or_problem}")
        if f == "member_covers" and isinstance(v, dict):
            v = {m: v[m] for m in MEMBERS if not is_empty(v.get(m))}
        ext[f] = None if is_empty(v) else v
        if ext[f] is not None and f not in quotes and quotes_in.get(f):
            quotes[f] = quotes_in[f]
        if remarks_in.get(f) and f not in remarks:
            remarks[f] = str(remarks_in[f])
    for f in FORMWORK_FIELDS:           # not in database.PARAMETERS: not asked for (as in v2)
        ext[f] = None
    ext["exposure"], ext["concrete_type"] = exposure, concrete_type
    quotes["exposure"] = f"Exposure condition determined outside the document: {exposure}"
    quotes["concrete_type"] = f"Concrete type determined outside the document: {concrete_type}"
    xrefs = [x for x in (parsed.get("cross_references") or []) if isinstance(x, dict)]
    ext["cross_references"] = xrefs
    ext["source_quotes"] = quotes
    ext["remarks"] = remarks
    ext["conflicts"] = []                # one call: nothing to merge (key kept for the v2 tools)
    info = {}
    for f in FIELDS:
        i = info_in.get(f) if isinstance(info_in.get(f), dict) else {}
        t = i.get("type") if i.get("type") in TYPES else ("not_found" if ext[f] is None else None)
        info[f] = {"type": t, "location": i.get("location") or ""}
    ext["field_info"] = info
    unknown = sorted(set(parsed) - set(FIELDS) - {"cross_references", "source_quotes", "remarks", "field_info"})
    return ext, {"table_notes": notes, "unknown_keys": unknown}


def check_locations(ext, doc):
    """Each " > " segment of a field's location must appear in the document (normalized)."""
    import verify
    doc_n = verify.norm(doc)
    rows = []
    for f, i in ext["field_info"].items():
        loc = i.get("location") or ""
        if not loc:
            continue
        segs = [s.strip() for s in loc.split(">") if s.strip()]
        missing = [s for s in segs if verify.norm(s) not in doc_n]
        rows.append({"field": f, "location": loc, "found": not missing, "missing_segments": missing})
    return rows


def run(run_name, role, exposure, concrete_type, table_mode, src, from_raw=None, thinking=None):
    from auditor import run_civion_audit
    from database import IS456_MASTER
    import verify

    out_dir = OUT / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    st = {}
    t = time.perf_counter()
    doc, st["prepare"] = prepare_doc(src)
    st["prepare"]["wall_s"] = round(time.perf_counter() - t, 3)
    (out_dir / "doc.md").write_text(doc, encoding="utf-8")
    system = prompt_v4.build_system(exposure, concrete_type, table_mode)
    user = prompt_v4.build_user(doc)
    (out_dir / "prompt_system.txt").write_text(system, encoding="utf-8")

    if from_raw:
        src_dir = OUT / from_raw
        parsed = json.loads((src_dir / "response.json").read_text(encoding="utf-8"))
        call = {**json.loads((src_dir / "run_stats.json").read_text(encoding="utf-8"))["call"], "reused_from": from_raw}
    else:
        model = model_id(role)
        left = remaining_today(model)
        print(f"[run_v4] {run_name}: model {model} ({role}); daily budget {used_today(model)} used, "
              f"{left} of {limits_for(model)['rpd']} left before this call")
        if left <= 0:
            raise SystemExit("No daily budget left for this model.")
        parsed, call = call_gemini(f"extract[{run_name}]", model, system, user, thinking=thinking)
        if parsed is None:
            write_json(out_dir / "run_stats.json", {"call": call, "steps": st})
            raise SystemExit(f"Call failed: {call['status']} {call.get('error')}")
        write_json(out_dir / "response.json", parsed)

    t = time.perf_counter()
    ext, post = to_contract(parsed, doc, exposure, concrete_type, table_mode)
    st["post_process"] = {**post, "wall_s": round(time.perf_counter() - t, 3)}
    write_json(out_dir / "extraction.json", ext)

    t = time.perf_counter()
    audit = run_civion_audit({k: v for k, v in ext.items() if k not in ("conflicts", "field_info")}, IS456_MASTER)
    st["audit"] = {"wall_s": round(time.perf_counter() - t, 3)}
    write_json(out_dir / "audit.json", audit)

    t = time.perf_counter()
    qc = verify.check_quotes(ext, doc)
    write_json(out_dir / "quote_check.json", qc)
    lc = check_locations(ext, doc)
    write_json(out_dir / "location_check.json", lc)
    st["checks"] = {"wall_s": round(time.perf_counter() - t, 3),
                    "quotes_found": sum(1 for q in qc if q["found"]), "quotes_not_found": sum(1 for q in qc if q["found"] is False),
                    "locations_found": sum(1 for r in lc if r["found"]), "locations_total": len(lc)}
    write_json(out_dir / "run_stats.json", {
        "args": {"input": str(src), "role": role, "exposure": exposure, "concrete_type": concrete_type,
                 "table_mode": table_mode, "from_raw": from_raw, "thinking": thinking},
        "call": call, "steps": st, "total_wall_s": round(time.perf_counter() - t_all, 2)})
    filled = sum(1 for f in FIELDS if ext[f] is not None)
    print(f"[run_v4] {run_name}: {filled}/{len(FIELDS)} fields filled, {len(ext['cross_references'])} references; "
          f"quotes {st['checks']['quotes_found']} found / {st['checks']['quotes_not_found']} not; "
          f"audit {audit['counts']}")
    if post["table_notes"] or post["unknown_keys"]:
        print(f"[run_v4] notes: {post}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--role", choices=["lite", "main"], default="lite")
    ap.add_argument("--exposure", default="Moderate")
    ap.add_argument("--concrete-type", default="Reinforced Concrete")
    ap.add_argument("--tables", choices=["python", "model"], default="python",
                    help="grading tables: model maps columns + Python reads cells, or model copies cells")
    ap.add_argument("--input", default=str(DEFAULT_IN))
    ap.add_argument("--from-raw", default=None, help="reuse output/<name>/response.json instead of calling")
    a = ap.parse_args()
    run(a.run_name, a.role, a.exposure, a.concrete_type, a.tables, a.input, a.from_raw)
