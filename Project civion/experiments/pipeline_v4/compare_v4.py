"""Compare v2 run4 with v4 runs, field by field: value, quote found, audit status;
plus the token / wall-time table in the format of report_v2.md section 7.

Adapted copy of experiments/shapes/compare_runs.py: that script only reads
folders under pipeline/output_v2/; this one takes "v2:<run>" or "v4:<run>".
The audit of every run is recomputed with the current auditor.py.

Usage (conda env civion, from pipeline_v4): python compare_v4.py v2:run4 v4:main1 v4:main2 > compare.md
"""
import json
import sys
from pathlib import Path

import gemini_call  # noqa: F401  (paths)
from gemini_call import HERE
from run_pipeline import audit_status  # experiments/pipeline
from auditor import run_civion_audit
from database import IS456_MASTER, PARAMETERS
import verify  # noqa: F401
from run_v4 import check_quotes

V2 = HERE.parent / "pipeline" / "output_v2"
V4 = HERE / "output"
MEMBERS = ["Beams", "Columns", "Slabs"]


def fmt(v, n=70):
    s = "null" if v is None else json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    s = s.replace("|", "\\|").replace("\n", " / ")
    return s if len(s) <= n else s[:n - 3] + "..."


def load(spec):
    kind, name = spec.split(":", 1)
    d = (V2 if kind == "v2" else V4) / name
    ext = json.loads((d / "extraction.json").read_text(encoding="utf-8"))
    text = (d / ("clean.md" if kind == "v2" else "doc.md")).read_text(encoding="utf-8")
    audit = run_civion_audit({k: v for k, v in ext.items() if k not in ("conflicts", "field_info")}, IS456_MASTER)
    quotes = {q["field"]: q for q in check_quotes(ext, text)}
    rows = {}
    for r in audit["ledger"]:
        rows.setdefault(r.get("Field") or r["Metric"], r)
    stats = json.loads((d / "run_stats.json").read_text(encoding="utf-8"))
    if kind == "v2":
        calls = [{"step": step_v2(c["name"]), "input": c.get("prompt_tokens") or 0,
                  "output": c.get("completion_tokens") or 0, "reasoning": None,
                  "total": c.get("total_tokens") or 0, "retries": c.get("retries") or 0,
                  "error": bool(c.get("error")), "wall_s": c.get("wall_s") or 0, "model": c.get("model")}
                 for c in stats["calls"]]
    else:
        c = stats["call"]
        calls = [{"step": "1 extract: whole document", "input": c.get("input_tokens") or 0,
                  "output": c.get("output_tokens") or 0, "reasoning": c.get("reasoning_tokens") or 0,
                  "total": c.get("total_tokens") or 0, "retries": c.get("retries") or 0,
                  "error": c.get("status") != "ok", "wall_s": c.get("wall_s") or 0, "model": c.get("model"),
                  "ok_wall_s": c.get("ok_attempt_wall_s") or c.get("wall_s") or 0}]
    return {"name": f"{kind} {name}", "kind": kind, "ext": ext, "audit": audit, "quotes": quotes, "rows": rows,
            "stats": stats, "calls": calls}


def step_v2(name):
    if name.startswith("localize"):
        return "1 section picking"
    if name.startswith("route"):
        return "2 routing"
    return "3 extract: " + name[len("extract["):].split("#")[0].split(".")[0].rstrip("]")


def value(run, f):
    base, _, sub = f.partition(".")
    v = run["ext"].get(base)
    return (v or {}).get(sub) if sub else v


def quote_state(run, f):
    base = f.split(".")[0]
    q = run["quotes"].get(base)
    if value(run, f) is None:
        return "-"
    if q is None:
        return "no quote"
    return "n/a" if q["found"] is None else ("yes" if q["found"] else "NO")


def fields():
    out = [f for f in PARAMETERS if PARAMETERS[f].get("from") != "derived" and f != "member_covers"]
    return out + [f"member_covers.{m}" for m in MEMBERS]


def field_table(runs):
    L = ["| field | " + " | ".join(f"{r['name']} value | quote | status" for r in runs) + " |",
         "|---|" + "---|---|---|" * len(runs)]
    for f in fields():
        cells = []
        for r in runs:
            row = r["rows"].get(f)
            cells += [fmt(value(r, f), 40), quote_state(r, f), audit_status(row) if row else "-"]
        L.append(f"| `{f}` | " + " | ".join(cells) + " |")
    return L


def token_table(runs):
    def tot(r, k):
        return sum((c.get(k) or 0) for c in r["calls"])
    L = ["| Metric | " + " | ".join(r["name"] for r in runs) + " |", "|---|" + "---:|" * len(runs)]

    def row(label, fn):
        L.append(f"| {label} | " + " | ".join(str(fn(r)) for r in runs) + " |")
    row("Model", lambda r: ", ".join(sorted({c.get("model") or "?" for c in r["calls"]})))
    row("API calls", lambda r: len(r["calls"]))
    row("Input (prompt) tokens", lambda r: f"{tot(r, 'input'):,}")
    row("Output tokens (v2: incl. hidden reasoning; v4: answer only)", lambda r: f"{tot(r, 'output'):,}")
    row("Reasoning tokens (v4: reported separately)", lambda r: "not reported" if r["kind"] == "v2" else f"{tot(r, 'reasoning'):,}")
    row("**Total tokens**", lambda r: f"**{tot(r, 'total'):,}**")
    row("Largest single call (total)", lambda r: f"{max(c['total'] for c in r['calls']):,}")
    row("429 / 5xx retries", lambda r: tot(r, "retries"))
    row("Call errors", lambda r: sum(1 for c in r["calls"] if c["error"]))
    row("Successful-attempt wall time (s) (v4 only; v2 has no per-attempt time)",
        lambda r: "-" if r["kind"] == "v2" else f"{sum(c['ok_wall_s'] for c in r['calls']):.1f}")
    row("LLM wall time incl. retries and backoff (s)", lambda r: f"{sum(c['wall_s'] for c in r['calls']):.1f}")
    row("Whole run wall time (s)", lambda r: r["stats"].get("total_wall_s"))
    L += ["", "**Per step: input / output tokens (calls)**", "",
          "| Step | " + " | ".join(r["name"] for r in runs) + " |", "|---|" + "---:|" * len(runs)]
    steps = list(dict.fromkeys(c["step"] for r in runs for c in r["calls"]))
    for s in sorted(steps):
        cells = []
        for r in runs:
            cs = [c for c in r["calls"] if c["step"] == s]
            cells.append(f"{sum(c['input'] for c in cs):,} / {sum(c['output'] + (c['reasoning'] or 0) for c in cs):,} ({len(cs)})"
                         if cs else "-")
        L.append(f"| {s} | " + " | ".join(cells) + " |")
    L.append("\nCell format: input / output (calls). For v4 the output includes reasoning (thinking) tokens, "
             "so it is comparable with v2's completion tokens.")
    return L


def consistency(a, b):
    same, diff = [], []
    for f in fields():
        (same if json.dumps(value(a, f), sort_keys=True) == json.dumps(value(b, f), sort_keys=True) else diff).append(f)
    sa = {f: audit_status(a["rows"][f]) for f in fields() if f in a["rows"]}
    sb = {f: audit_status(b["rows"][f]) for f in fields() if f in b["rows"]}
    sdiff = [f for f in sa if sa[f] != sb.get(f)]
    L = [f"Same value in both: {len(same)} of {len(same) + len(diff)} fields. Same audit status: "
         f"{len(sa) - len(sdiff)} of {len(sa)}."]
    for f in diff:
        L.append(f"- `{f}`: {fmt(value(a, f), 60)} vs {fmt(value(b, f), 60)}")
    return L


def main(specs):
    runs = [load(s) for s in specs]
    L = ["# v2 vs v4 on BLR (generated by compare_v4.py)", ""]
    for r in runs:
        L.append(f"- {r['name']}: current-auditor counts {r['audit']['counts']} ({r['audit']['summary']}); "
                 f"quotes found {sum(1 for q in r['quotes'].values() if q['found'])}, "
                 f"not found {sum(1 for q in r['quotes'].values() if q['found'] is False)}; "
                 f"{len(r['ext'].get('cross_references') or [])} references")
    L += ["", "## Field by field", "", "quote: yes = verbatim in the document (verify.py), NO = not found, "
          "no quote = value without a quote, n/a = stamped from CLI.", ""] + field_table(runs)
    v4 = [r for r in runs if r["kind"] == "v4"]
    if len(v4) >= 2:
        L += ["", f"## Consistency: {v4[0]['name']} vs {v4[1]['name']}", ""] + consistency(v4[0], v4[1])
    for r in runs:
        bad = [q for q in r["quotes"].values() if q["found"] is False]
        L += ["", f"### {r['name']}: quotes not found ({len(bad)})"]
        L += [f"- `{q['field']}`: \"{fmt(q['quote'], 110)}\" - {fmt('; '.join(map(str, q.get('missing_fragments') or [])), 110)}"
              for q in bad]
        L += [f"\nReferences: " + "; ".join(f"{x.get('parameter')} -> {x.get('points_to') or x.get('referenced_code')}"
                                           for x in r["ext"].get("cross_references") or [])]
        rem = r["ext"].get("remarks") or {}
        if rem:
            L += ["Remarks:"] + [f"- `{k}`: {fmt(v, 160)}" for k, v in rem.items()]
    L += ["", "## Tokens and wall time (MEASURED: API usage fields)", ""] + token_table(runs)
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
