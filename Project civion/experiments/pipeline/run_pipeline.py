"""STEP 5 - run steps 1-4, then auditor.run_civion_audit(), and write report.md.

Outputs (in ./output): clean.md, sections.json, outline.txt, selected.json,
localized.md, not_selected.txt, extraction.json, audit.json, run_stats.json,
and ./report.md.

The "missing parameter" analysis in the report (does the value exist in
clean.md?) needs a human/agent search of the document; it is read from
missing_analysis.md if present, otherwise the report says it is pending.

Usage: python run_pipeline.py [--exposure Moderate] [--concrete-type "Reinforced Concrete"]
       python run_pipeline.py --report-only   (rebuild report.md from saved outputs)
"""
import sys
import time

from common import CALL_LOG, HERE, OUT_DIR, est_tokens, read_json, write_json
import clean
import sections
import localize
import extract


def audit_status(row):
    if row["Status"] == "Pass":
        return "PASS"
    if row["Status"] == "Fail":
        return "FAIL"
    if row["Extracted Value"] == "Not Provided":
        return "MISSING"
    return "WARNING"


def run(exposure, concrete_type, max_call_tokens):
    from auditor import run_civion_audit
    from database import IS456_MASTER

    stats = {"steps": {}}
    t = time.perf_counter(); stats["steps"]["clean"] = {**clean.main(), "wall_s": round(time.perf_counter() - t, 3)}
    t = time.perf_counter(); stats["steps"]["sections"] = {**sections.main(), "wall_s": round(time.perf_counter() - t, 3)}
    stats["steps"]["localize"] = localize.main()
    merged, info = extract.main(exposure, concrete_type, max_call_tokens)
    stats["steps"]["extract"] = info
    write_json(OUT_DIR / "extraction.json", merged)

    t = time.perf_counter()
    # The auditor ignores unknown keys; hand it the extraction without the
    # merge bookkeeping, exactly like the app's parser output.
    audit = run_civion_audit({k: v for k, v in merged.items() if k != "_candidates"}, IS456_MASTER)
    stats["steps"]["audit"] = {"wall_s": round(time.perf_counter() - t, 3)}
    write_json(OUT_DIR / "audit.json", audit)
    stats["calls"] = CALL_LOG
    stats["args"] = {"exposure": exposure, "concrete_type": concrete_type, "max_call_tokens": max_call_tokens}
    write_json(OUT_DIR / "run_stats.json", stats)
    return stats


def fmt(v):
    if v is None:
        return "null"
    s = str(v).replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= 140 else s[:137] + "..."


# Audit ledger metric -> extraction field(s) it reads.
METRIC_FIELDS = {
    "Concrete Type": "concrete_type", "Environmental Exposure": "exposure", "Cement Type": "cement_type",
    "Soil Total SO3": "soil_total_so3_percent", "Soil Extract SO3": "soil_extract_2_1_so3_gl",
    "Groundwater SO3": "groundwater_so3_gl", "Sulfate Cement Type": "cement_type",
    "Freezing and Thawing": "freezing_thawing_exposure", "Concrete Grade": "specified_grade",
    "Min Cement Content": "specified_min_cement", "Max Cement Content": "specified_max_cement",
    "W/C Ratio": "specified_wc", "Standard Deviation (sigma)": "specified_sigma",
    "Characteristic Strength": "specified_characteristic_strength",
    "Fire Resistance Rating": "fire_resistance_rating", "Beams Cover": "member_covers.Beams",
    "Columns Cover": "member_covers.Columns", "Slabs Cover": "member_covers.Slabs",
    "Mixing Time": "mixing_time_minutes", "Transportation Time": "transport_time_minutes",
    "Compaction Method": "compaction_method", "Curing Days": "curing_days", "Slump": "specified_slump_mm",
    "Water pH": "water_ph", "Water - Organic Solids": "water_organic_mg_l",
    "Water - Inorganic Solids": "water_inorganic_mg_l", "Water - Sulphates": "water_sulphates_mg_l",
    "Water - Chlorides": "water_chlorides_mg_l", "Water - Suspended Matter": "water_suspended_matter_mg_l",
    "Chloride Content": "measured_chloride_content", "Sulphate (SO3) Content": "measured_so3_percent",
    "Total Volume": "total_volume_m3", "Cube Size": "sampling_cube_size_mm",
    "Sampling Sets": "specified_sampling_sets",
}


def field_value(ext, field):
    if field.startswith("member_covers."):
        return (ext.get("member_covers") or {}).get(field.split(".", 1)[1])
    return ext.get(field)


def report():
    stats = read_json(OUT_DIR / "run_stats.json")
    ext = read_json(OUT_DIR / "extraction.json")
    audit = read_json(OUT_DIR / "audit.json")
    sel = read_json(OUT_DIR / "selected.json")
    secs = read_json(OUT_DIR / "sections.json")
    raw_md = (extract.PROJECT_ROOT / "experiments" / "parse_test" / "docling_output.md").read_text(encoding="utf-8")
    clean_md = (OUT_DIR / "clean.md").read_text(encoding="utf-8")
    loc_md = (OUT_DIR / "localized.md").read_text(encoding="utf-8")
    quotes = ext.get("source_quotes") or {}
    st = stats["steps"]

    L = []
    L.append("# Civion localization + extraction pipeline - BLR run report\n")
    L.append(f"Args: exposure=`{stats['args']['exposure']}`, concrete_type=`{stats['args']['concrete_type']}`, "
             f"max tokens/call (target)=`{stats['args']['max_call_tokens']}`. "
             f"Model: `{stats['calls'][0]['model'] if stats['calls'] else '?'}`.\n")
    L.append("Legend: **MEASURED** = counted by code or taken from the Groq API `usage` field. "
             "**EST** = estimate (chars / 4).\n")

    L.append("## 1. Document size: whole doc vs localized\n")
    L.append("| Text | Chars (MEASURED) | Tokens (EST, chars/4) | % of clean.md |")
    L.append("|---|---:|---:|---:|")
    for name, txt in [("docling_output.md (raw)", raw_md), ("clean.md (whole doc)", clean_md),
                      ("localized.md", loc_md)]:
        L.append(f"| {name} | {len(txt):,} | {est_tokens(txt):,} | {100 * len(txt) / len(clean_md):.1f}% |")
    old = clean_md[:12000]
    L.append(f"\nFor comparison, today's parser.py sends `clean_text[:12000]` (~{est_tokens(old):,} EST tokens) of its own pdfplumber text.\n")
    c = st["clean"]
    L.append(f"clean.py removed {c['image_markers_removed']} `<!-- image -->` markers and "
             f"{sum(c['repeated_lines_removed'].values())} repeated header/footer lines "
             f"(no normalized line < 120 chars repeats 3+ times in this doc once images are gone).\n")

    L.append("## 2. API calls (MEASURED usage) and wall time\n")
    L.append("| Call | reasoning_effort | Prompt tok | Completion tok | Total tok | Text sent (chars) | Retries (429) | Wall s | Error |")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    tot_p = tot_c = 0
    for call in stats["calls"]:
        tot_p += call["prompt_tokens"] or 0
        tot_c += call["completion_tokens"] or 0
        L.append(f"| {call['name']} | {call.get('reasoning_effort')} | {call['prompt_tokens']} | {call['completion_tokens']} | "
                 f"{call['total_tokens']} | {call.get('text_chars', '-')} | {call['retries']} | {call['wall_s']} | {call['error'] or ''} |")
    L.append(f"| **Total** | | **{tot_p:,}** | **{tot_c:,}** | **{tot_p + tot_c:,}** | | | | |")
    over = [c for c in stats["calls"] if (c["total_tokens"] or 0) > stats["args"]["max_call_tokens"]]
    L.append(f"\nCalls over the {stats['args']['max_call_tokens']}-token target (MEASURED): "
             f"{', '.join(c['name'] + ' (' + str(c['total_tokens']) + ')' for c in over) or 'none'}. "
             "Completion tokens include gpt-oss hidden reasoning tokens.\n")
    L.append("Wall time per step (MEASURED; extract includes the deliberate TPM pacing sleeps):\n")
    L.append("| Step | Wall s |")
    L.append("|---|---:|")
    for k in ["clean", "sections", "localize", "extract", "audit"]:
        L.append(f"| {k} | {st[k]['wall_s']} |")
    L.append(f"| **total** | **{sum(st[k]['wall_s'] for k in ['clean', 'sections', 'localize', 'extract', 'audit']):.2f}** |\n")

    L.append("## 3. Localization\n")
    n_sec = len(secs)
    n_tab = sum(len(s["tables"]) for s in secs)
    sel_secs = [s for s in sel["selected"] if s["kind"] == "section"]
    sel_ids = {s["id"] for s in sel["selected"]}
    n_tab_sel = sum(len(s["tables"]) for s in secs if s["id"] in sel_ids) + sum(1 for s in sel["selected"] if s["kind"] == "table")
    L.append(f"- Sections: {n_sec} total, **{len(sel_secs)} selected**, {n_sec - len(sel_secs)} not selected "
             f"({sum(1 for s in secs if not s['text'].strip())} of all sections have no body text, e.g. PART headings).")
    L.append(f"- Tables: {n_tab} total, {n_tab_sel} included in localized.md.")
    L.append(f"- Parents added by the deterministic 'picked child -> keep parent text' rule: {sel.get('parents_added_by_rule') or 'none'}.")
    L.append(f"- Unknown ids returned by the model: {sel.get('unknown_ids_returned') or 'none'}.")
    by_group = {}
    for s in sel["selected"]:
        by_group.setdefault(s["group"], []).append(s["id"])
    for g, ids in by_group.items():
        L.append(f"- `{g}`: {', '.join(ids)}")
    L.append("\nSelected headings:\n")
    L.append("```")
    for s in sel["selected"]:
        L.append(f"{s['id']} [{s['group']}] {' > '.join(s['heading_path'])}")
    L.append("```\n")
    L.append("Not selected (full list also in `output/not_selected.txt`):\n")
    L.append("```")
    L.append((OUT_DIR / "not_selected.txt").read_text(encoding="utf-8").rstrip())
    L.append("```\n")

    L.append("## 4. Extracted parameters vs audit\n")
    L.append("| Audit metric | Parameter | Extracted value | Source quote | Audit status |")
    L.append("|---|---|---|---|---|")
    missing = []
    for row in audit["ledger"]:
        metric = row["Metric"]
        status = audit_status(row)
        field = METRIC_FIELDS.get(metric)
        if field is None and metric.endswith("(Cross-Reference)"):
            field = "cross_references"
        if metric.startswith("Formwork"):
            field = "formwork_* (skipped by design)"
        val = field_value(ext, field) if field in METRIC_FIELDS.values() else row["Extracted Value"]
        q = quotes.get(field.split(".")[0], "") if field in METRIC_FIELDS.values() else ""
        if field == "cross_references":
            q = next((x.get("source_quote", "") for x in ext.get("cross_references", [])
                      if metric.lower().startswith(str(x.get("parameter", "")).replace("_", " ").lower())), "")
        L.append(f"| {metric} | `{field}` | {fmt(val)} | {fmt(q)} | {status} |")
        if status == "MISSING":
            missing.append((metric, field))
    counts = {}
    for row in audit["ledger"]:
        counts[audit_status(row)] = counts.get(audit_status(row), 0) + 1
    L.append("")
    L.append("Note: `exposure` and `concrete_type` are given from outside (CLI args), as in the app. "
             "The auditor fills in `exposure`='Moderate' and `cement_type`='OPC' defaults when they are null, "
             "so 'Cement Type' can show PASS even without an extracted value; check the value column.\n")
    if ext.get("cross_references"):
        L.append("Cross-references extracted:\n")
        for x in ext["cross_references"]:
            L.append(f"- {x.get('parameter')} -> {x.get('referenced_code')}: \"{fmt(x.get('source_quote'))}\"")
        L.append("")
    conflicts = {k: v for k, v in (ext.get("_candidates") or {}).items()
                 if len({str(c['value']) for c in v}) > 1}
    if conflicts:
        L.append("Fields where different calls returned different values (merge picked the owning group's / first):\n")
        for k, v in conflicts.items():
            L.append(f"- `{k}`: " + "; ".join(f"{c['value']} ({c['group']}#{c['chunk']})" for c in v))
        L.append("")

    L.append("## 5. MISSING parameters - is the value in the document?\n")
    missing_fields = list(dict.fromkeys(f for _, f in missing))
    L.append(f"MISSING audit rows: {len(missing)}. Params: " + ", ".join(f"`{f}`" for f in missing_fields) + "\n")
    ma = HERE / "missing_analysis.md"
    L.append(ma.read_text(encoding="utf-8").strip() if ma.exists() else "_Pending: manual search of clean.md not written yet._")
    L.append("")

    L.append("## 6. Audit counts\n")
    L.append("| Status | Count |")
    L.append("|---|---:|")
    for k in ["PASS", "FAIL", "MISSING", "WARNING"]:
        L.append(f"| {k} | {counts.get(k, 0)} |")
    L.append(f"| total ledger rows | {len(audit['ledger'])} |")
    L.append(f"\nauditor.py's own counts (MISSING is counted as 'warning' there): {audit['counts']}\n")
    hook = st["extract"]["fallback_hook"]
    L.append("## 7. Fallback hook\n")
    L.append(f"`experiments/fallback_search/keywords.json` found: **{hook['keywords_found']}**"
             + ("" if hook["keywords_found"] else " (so the hook did not fire)")
             + ". The fallback search itself is not implemented. "
             f"Null params it would hand over: {', '.join(hook['null_params']) or 'none'}.\n")
    (HERE / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[report] wrote {HERE / 'report.md'}")


if __name__ == "__main__":
    if "--report-only" in sys.argv:
        report()
    else:
        a = extract.cli_args([x for x in sys.argv[1:]])
        run(a.exposure, a.concrete_type, a.max_call_tokens)
        report()
