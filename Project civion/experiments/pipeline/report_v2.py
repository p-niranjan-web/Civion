"""Build report_v2.md from v1_results/ and output_v2/run1 (+ run2 if present).

The MISSING-parameter search of clean.md is a human/agent judgement; it is
read from missing_analysis_v2.md if present.
Usage: python report_v2.py
"""
import json

from common import HERE, est_tokens, read_json
from groups import ALL_PARAMS, GROUPS, PARAM_GROUP
from run_pipeline import METRIC_FIELDS, audit_status, field_value

V1 = HERE / "v1_results"
V2 = HERE / "output_v2"


def fmt(v, n=120):
    if v is None:
        return "null"
    s = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= n else s[:n - 3] + "..."


def load_run(d, v1=False):
    if not (d / "audit.json").exists():
        return None
    r = {"dir": d, "ext": read_json(d / "extraction.json"), "audit": read_json(d / "audit.json"),
         "stats": read_json(d / "run_stats.json")}
    r["calls"] = r["stats"]["calls"]
    r["status"] = {}
    for row in r["audit"]["ledger"]:
        r["status"].setdefault(METRIC_FIELDS.get(row["Metric"], row["Metric"]), audit_status(row))
    r["counts"] = {}
    for row in r["audit"]["ledger"]:
        k = audit_status(row)
        r["counts"][k] = r["counts"].get(k, 0) + 1
    clean_md = (d / "clean.md").read_text(encoding="utf-8")
    r["clean_chars"] = len(clean_md)
    if v1:
        r["sent_chars"] = len((d / "localized.md").read_text(encoding="utf-8"))
        r["unique_chars"] = r["sent_chars"]
        st = r["stats"]["steps"]
        r["wall"] = {"total": sum(st[k]["wall_s"] for k in ["clean", "sections", "localize", "extract", "audit"]),
                     "extract": st["extract"]["wall_s"], "localize": st["localize"]["wall_s"]}
        r["quote_check"] = None
    else:
        ext_calls = [c for c in r["calls"] if c["name"].startswith("extract")]
        r["sent_chars"] = sum(c.get("text_chars", 0) for c in ext_calls)
        units = read_json(d / "units.json")
        routing = read_json(d / "routing.json")
        r["routing"] = routing
        r["units"] = units
        r["unique_chars"] = sum(len(u["text"]) for u in units if routing["routing"].get(u["id"]))
        st = r["stats"]["steps"]
        r["wall"] = {"total": r["stats"]["total_wall_s"], "extract": st["extract"]["wall_s"],
                     "localize": st["stage_a"]["wall_s"], "route": st["stage_b"]["wall_s"]}
        r["quote_check"] = read_json(d / "quote_check.json")
        r["scope"] = read_json(d / "scope.json")
    r["found"] = sum(1 for p in ALL_PARAMS if p != "member_covers" and r["ext"].get(p) is not None) + \
        sum(1 for m in ["Beams", "Columns", "Slabs"] if (r["ext"].get("member_covers") or {}).get(m) is not None)
    return r


def tok(calls, key):
    return sum(c.get(key) or 0 for c in calls)


def main():
    v1 = load_run(V1, v1=True)
    runs = {n: load_run(V2 / n) for n in ["run1", "run2"]}
    runs = {n: r for n, r in runs.items() if r}
    r1 = runs["run1"]
    cols = [("v1", v1)] + [(f"v2 {n}", r) for n, r in runs.items()]
    L = ["# Civion pipeline v2 - BLR report\n"]
    L.append(f"Args: exposure=`{r1['stats']['args']['exposure']}`, concrete_type=`{r1['stats']['args']['concrete_type']}`, "
             f"target max tokens/call `{r1['stats']['args']['max_call_tokens']}`, model `{r1['calls'][0]['model']}`.\n")
    L.append("**MEASURED** = counted by code / Groq API `usage` field. **EST** = chars/4 estimate. "
             "v1 numbers come from `v1_results/` (the committed v1 run), not a re-run.\n")

    tk = HERE / "takeaways_v2.md"
    if tk.exists():
        L.append("## Takeaways\n")
        L.append(tk.read_text(encoding="utf-8").strip() + "\n")
    # ---------------------------------------------------------------- 1
    L.append("## 1. v1 vs v2 summary\n")
    L.append("| Metric | " + " | ".join(n for n, _ in cols) + " |")
    L.append("|---|" + "---:|" * len(cols))

    def row(label, f):
        L.append(f"| {label} | " + " | ".join(str(f(r)) for _, r in cols) + " |")
    row("API calls (MEASURED)", lambda r: len(r["calls"]))
    row("Prompt tokens, total (MEASURED)", lambda r: f"{tok(r['calls'], 'prompt_tokens'):,}")
    row("Completion tokens, total (MEASURED)", lambda r: f"{tok(r['calls'], 'completion_tokens'):,}")
    row("**Total tokens (MEASURED)**", lambda r: f"**{tok(r['calls'], 'total_tokens'):,}**")
    row("Largest single call, tokens (MEASURED)", lambda r: max(c.get("total_tokens") or 0 for c in r["calls"]))
    row("Calls over 5,000 tokens (MEASURED)", lambda r: sum(1 for c in r["calls"] if (c.get("total_tokens") or 0) > 5000))
    row("429 retries (MEASURED)", lambda r: sum(c.get("retries", 0) for c in r["calls"]))
    row("Call errors", lambda r: sum(1 for c in r["calls"] if c.get("error")))
    row("Wall time total, s (MEASURED, incl. TPM pacing sleeps)", lambda r: f"{r['wall']['total']:.0f}")
    row("  of which extraction step, s", lambda r: f"{r['wall']['extract']:.0f}")
    row("Whole doc (clean.md), chars", lambda r: f"{r['clean_chars']:,}")
    row("Chars sent to extraction calls (incl. repeats)", lambda r: f"{r['sent_chars']:,} ({100 * r['sent_chars'] / r['clean_chars']:.0f}%)")
    row("Unique doc chars sent to extraction", lambda r: f"{r['unique_chars']:,} ({100 * r['unique_chars'] / r['clean_chars']:.0f}%)")
    row("Parameters found (of 28: 26 params, covers counted per member)", lambda r: r["found"])
    row("Cross-references", lambda r: len(r["ext"].get("cross_references") or []))
    for k in ["PASS", "FAIL", "MISSING", "WARNING"]:
        row(f"Audit {k}", lambda r, k=k: r["counts"].get(k, 0))
    row("Source quotes not found in clean.md (deterministic check)",
        lambda r: "-" if r["quote_check"] is None else sum(1 for q in r["quote_check"] if q["found"] is False))
    L.append("\nv1's quote check (run afterwards with verify.py): 1 quote not in the document "
             "(`concrete_type`, model-written; fixed in v2).\n")

    # ---------------------------------------------------------------- 2
    L.append("## 2. Calls (MEASURED usage)\n")
    for name, r in cols:
        L.append(f"**{name}**\n")
        L.append("| Call | effort | Prompt | Completion | Total | Text chars | Units | Retries | Wall s | Error |")
        L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for c in r["calls"]:
            L.append(f"| {c['name']} | {c.get('reasoning_effort')} | {c['prompt_tokens']} | {c['completion_tokens']} | "
                     f"{c['total_tokens']} | {c.get('text_chars', '-')} | {c.get('n_units', '-')} | {c['retries']} | "
                     f"{c['wall_s']} | {c.get('error') or ''} |")
        L.append("")
    L.append("Wall s per call includes the pacing sleep before the call (TPM budget 7,000/min).\n")

    # ---------------------------------------------------------------- 3
    L.append("## 3. Localization and routing (v2)\n")
    for n, r in runs.items():
        sc = r["scope"]
        added = {k: v for k, v in sc["reasons"].items() if v != "stage_a"}
        rt = r["routing"]
        L.append(f"**{n}**: Stage A picked {sum(1 for v in sc['reasons'].values() if v == 'stage_a')} sections; "
                 f"safety nets added {len(added)} ({', '.join(f'{k}:{v}' for k, v in added.items()) or 'none'}). "
                 f"{len(r['units'])} units -> {len(r['units']) - len(rt['unrouted_units'])} routed to >=1 group, "
                 f"{len(rt['unrouted_units'])} to none. Retried ids: {len(rt['retried_units'])}, "
                 f"defaulted to all groups: {len(rt['defaulted_to_all_groups'])}.\n")
        L.append("| Group | Units | Text chars | Text tokens (EST) | Extraction calls | Prompt tokens (MEASURED) |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for g, v in rt["per_group"].items():
            gc = [c for c in r["calls"] if c.get("group") == g]
            L.append(f"| {g} | {v['units']} | {v['chars']:,} | {v['est_tokens']:,} | {len(gc)} | {tok(gc, 'prompt_tokens'):,} |")
        L.append("")

    fname = "v2 run2" if "run2" in runs else "v2 run1"
    rf = runs.get("run2") or r1
    # ---------------------------------------------------------------- 4
    L.append("## 4. Per-parameter results\n")
    hdr = f"| Parameter | Group | v1 value | v1 audit | " + " | ".join(f"{n} value" for n in runs) + \
          f" | {fname} source quote | quote in doc? | {fname} audit |"
    L.append(hdr)
    L.append("|" + "---|" * (hdr.count("|") - 1))
    q1 = {q["field"]: q for q in rf["quote_check"]}
    fields = ALL_PARAMS[:]
    fields.remove("member_covers")
    fields += [f"member_covers.{m}" for m in ["Beams", "Columns", "Slabs"]]
    for f in fields:
        base = f.split(".")[0]
        q = (rf["ext"].get("source_quotes") or {}).get(base)
        qc = q1.get(base)
        found = "-" if not q else ("yes" if qc and qc["found"] else "NO" if qc else "?")
        if field_value(rf["ext"], f) is None:
            q, found = None, "-"
        L.append(f"| `{f}` | {PARAM_GROUP[base]} | {fmt(field_value(v1['ext'], f), 40)} | {v1['status'].get(f, '-')} | "
                 + " | ".join(fmt(field_value(r['ext'], f), 40) for r in runs.values())
                 + f" | {fmt(q, 150) if q else ''} | {found} | {rf['status'].get(f, '-')} |")
    L.append("\nNot extracted by design: formwork (5 audit rows, always MISSING), and exposure / concrete_type / "
             "site SO3, which are supplied from outside (the 3 site-SO3 audit rows stay MISSING).\n")

    for n, r in runs.items():
        if r["ext"].get("conflicts"):
            L.append(f"**Conflicts between batches ({n})** - first value in document order used, all kept:\n")
            for c in r["ext"]["conflicts"]:
                L.append(f"- `{c['field']}`: " + "; ".join(f"{fmt(x['value'], 30)} (batch {x['batch']})" for x in c["candidates"]))
            L.append("")
    L.append(f"Cross-references ({fname}):\n")
    for x in rf["ext"].get("cross_references") or []:
        qc = next((q for q in rf["quote_check"] if q["field"] == f"cross_ref:{x.get('parameter')}->{x.get('referenced_code')}"), None)
        L.append(f"- {x.get('parameter')} -> {x.get('referenced_code')}: \"{fmt(x.get('source_quote'), 140)}\""
                 + ("" if not qc or qc["found"] else "  **(quote NOT found in clean.md)**"))
    bad = [q for q in rf["quote_check"] if q["found"] is False]
    L.append(f"\nQuote check ({fname}): {sum(1 for q in rf['quote_check'] if q['found'])} found, {len(bad)} not found"
             + ("".join(f"\n- NOT FOUND `{q['field']}`: \"{fmt(q['quote'], 150)}\"" for q in bad)) + "\n")

    # ---------------------------------------------------------------- 5
    L.append(f"## 5. MISSING parameters ({fname}) - is the value in clean.md?\n")
    ma = HERE / "missing_analysis_v2.md"
    L.append(ma.read_text(encoding="utf-8").strip() if ma.exists() else "_Pending._")
    L.append("")

    # ---------------------------------------------------------------- 6
    L.append("## 6. Consistency: run1 vs run2\n")
    L.append("**Caveat:** run2 is not an identical re-run. Between the runs the extraction prompt's "
             "CROSS-REFERENCES paragraph was restored to parser.py's wording (run1 returned 0 cross-references; "
             "see CHANGES.md). Stage A, units and routing code are identical, so scope/routing differences are "
             "pure LLM nondeterminism; extracted-value differences may partly come from the prompt change.\n")
    if "run2" not in runs:
        L.append("Run 2 was not executed.\n")
    else:
        r2 = runs["run2"]
        s1, s2 = set(r1["scope"]["scope"]), set(r2["scope"]["scope"])
        L.append(f"- In-scope sections: run1 {len(s1)}, run2 {len(s2)}; only in run1: {sorted(s1 - s2) or 'none'}; "
                 f"only in run2: {sorted(s2 - s1) or 'none'}.")
        rt1, rt2 = r1["routing"]["routing"], r2["routing"]["routing"]
        common_u = set(rt1) & set(rt2)
        diff_u = [u for u in sorted(common_u) if set(rt1[u]) != set(rt2[u])]
        L.append(f"- Units: run1 {len(rt1)}, run2 {len(rt2)}; common {len(common_u)}; "
                 f"common units with different group tags: {len(diff_u)} ({100 * len(diff_u) / max(len(common_u), 1):.0f}%).")
        vdiff = [f for f in fields if json.dumps(field_value(r1["ext"], f)) != json.dumps(field_value(r2["ext"], f))]
        L.append(f"- Extracted values that differ: {len(vdiff)}" + "".join(
            f"\n  - `{f}`: run1 {fmt(field_value(r1['ext'], f), 40)} vs run2 {fmt(field_value(r2['ext'], f), 40)}" for f in vdiff))
        sdiff = [k for k in set(r1["status"]) | set(r2["status"]) if r1["status"].get(k) != r2["status"].get(k)]
        L.append(f"- Audit statuses that differ: {len(sdiff)}" + "".join(
            f"\n  - `{k}`: {r1['status'].get(k)} vs {r2['status'].get(k)}" for k in sorted(sdiff)))
        L.append(f"- Audit counts: run1 {r1['counts']} vs run2 {r2['counts']}.")
        L.append(f"- Total tokens (MEASURED): run1 {tok(r1['calls'], 'total_tokens'):,} vs run2 {tok(r2['calls'], 'total_tokens'):,}.\n")
    (HERE / "report_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[report_v2] wrote {HERE / 'report_v2.md'}")


if __name__ == "__main__":
    main()
