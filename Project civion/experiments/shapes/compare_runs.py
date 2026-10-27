"""Compare two pipeline runs field by field: extracted value, quote check, audit status.

Usage (from experiments/pipeline): python ../shapes/compare_runs.py run2 run3 > ../shapes/run2_vs_run3.md
The audit of BOTH runs is recomputed with the current auditor.py, so status
differences come from the extraction; the stored audit.json of the old run is
reported separately (old auditor).
"""
import json
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
from common import read_json  # noqa: E402  (also puts the project root on sys.path)
from run_pipeline import audit_status  # noqa: E402
from auditor import run_civion_audit  # noqa: E402
from database import IS456_MASTER, PARAMETERS  # noqa: E402
import verify  # noqa: E402


def fmt(v, n=70):
    s = "null" if v is None else json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    s = s.replace("|", "\\|").replace("\n", " / ")
    return s if len(s) <= n else s[:n - 3] + "..."


def load(name):
    d = PIPE / "output_v2" / name
    ext = read_json(d / "extraction.json")
    audit = run_civion_audit({k: v for k, v in ext.items() if k != "conflicts"}, IS456_MASTER)
    stored = read_json(d / "audit.json")
    clean = (d / "clean.md").read_text(encoding="utf-8")
    quotes = {q["field"]: q for q in verify.check_quotes(ext, clean)}
    rows = {}
    for r in audit["ledger"]:
        rows.setdefault(r.get("Field") or r["Metric"], r)
    stats = read_json(d / "run_stats.json")
    return {"ext": ext, "audit": audit, "stored": stored, "quotes": quotes, "rows": rows, "stats": stats}


def main(a, b):
    A, B = load(a), load(b)
    L = [f"# {a} vs {b} (BLR)\n",
         f"Audit recomputed with the current auditor for both runs. Stored counts: {a} {A['stored']['counts']}, "
         f"{b} {B['stored']['counts']}.\n",
         f"Current-auditor counts: {a} {A['audit']['counts']} ({A['audit']['summary']}); "
         f"{b} {B['audit']['counts']} ({B['audit']['summary']}).\n",
         f"Tokens (MEASURED): {a} {sum(c.get('total_tokens') or 0 for c in A['stats']['calls']):,} in "
         f"{len(A['stats']['calls'])} calls; {b} {sum(c.get('total_tokens') or 0 for c in B['stats']['calls']):,} in "
         f"{len(B['stats']['calls'])} calls.\n",
         f"| field | {a} value | {b} value | {b} quote in doc? | {a} status | {b} status | {b} remark |",
         "|---|---|---|---|---|---|---|"]
    fields = [f for f in PARAMETERS if PARAMETERS[f].get("from") != "derived" and f != "member_covers"]
    fields += [f"member_covers.{m}" for m in ["Beams", "Columns", "Slabs"]]
    for f in fields:
        base, _, sub = f.partition(".")
        va, vb = A["ext"].get(base), B["ext"].get(base)
        if sub:
            va, vb = (va or {}).get(sub), (vb or {}).get(sub)
        q = B["quotes"].get(base)
        qtxt = "-" if vb is None or q is None or q["found"] is None else ("yes" if q["found"] else "NO")
        ra, rb = A["rows"].get(f), B["rows"].get(f)
        remark = (B["ext"].get("remarks") or {}).get(base, "")
        L.append(f"| `{f}` | {fmt(va, 45)} | {fmt(vb, 45)} | {qtxt} | {audit_status(ra) if ra else '-'} | "
                 f"{audit_status(rb) if rb else '-'} | {fmt(remark, 90)} |")
    L.append(f"\n**References ({b})**\n")
    for x in B["ext"].get("cross_references") or []:
        L.append(f"- {x.get('parameter')} -> {x.get('points_to') or x.get('referenced_code')}: \"{fmt(x.get('source_quote'), 120)}\"")
    bad = [q for q in B["quotes"].values() if q["found"] is False]
    L.append(f"\n**Quote check ({b})**: {sum(1 for q in B['quotes'].values() if q['found'])} found, {len(bad)} not found")
    for q in bad:
        L.append(f"- `{q['field']}`: \"{fmt(q['quote'], 120)}\" - {fmt('; '.join(map(str, q.get('missing_fragments') or [])), 120)}")
    tq = [q for q in B["quotes"].values() if q.get("kind") == "table"]
    L.append(f"\nTable quotes: {sum(1 for q in tq if q['found'])} of {len(tq)} pass; number not in quoted row: "
             f"{[q['field'] for q in tq if q.get('value_in_row') is False] or 'none'}")
    L.append(f"\n**Non-pass rows ({b}, current auditor)**\n")
    for r in B["audit"]["ledger"]:
        if r["Status"] in ("Fail", "Warning"):
            L.append(f"- {audit_status(r)} {r['Metric']}: {fmt(r['Extracted Value'], 60)} | {fmt(r['Requirement'], 160)}")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
