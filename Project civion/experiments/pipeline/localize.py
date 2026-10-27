"""STEP 3 - localize the relevant parts of the document with ONE Groq call.

The model sees ONLY outline.txt (ids + headings/captions, no body text) and
returns the ids that are in scope, each tagged with the extraction topic
group it belongs to (used by extract.py to batch the calls).

Outputs: selected.json, localized.md, not_selected.txt.
Usage: python localize.py
"""
import time
from pathlib import Path

from common import OUT_DIR, call_groq, read_json, write_json

GROUPS = {
    "materials": "cement types, mixing/curing water quality, admixtures, aggregates",
    "durability_grade": "concrete grades/characteristic strength, durability (cement content, w/c ratio, exposure and sulphate tables)",
    "production_curing": "mix design, trial mixes, batching, mixing, transport, placing, compaction, slump/workability, joints, curing, mass concrete",
    "cover_sampling": "nominal cover to reinforcement, sampling/testing frequency, cube tests, acceptance criteria",
}

SYSTEM = ("You select document sections for a concrete-specification compliance checker. "
          "Output STRICTLY valid JSON.")

PROMPT = """Below is the OUTLINE of a construction specification: one line per
section ("S###") or table ("S###.T#"), with indentation showing nesting. You
see only headings/captions, not the body text.

Return the ids of every section or table whose content is likely to state
requirements IN SCOPE:
  IN: concrete grades / characteristic strength; durability (minimum cement
      content, maximum water-cement ratio, exposure classes, sulphate-attack
      tables); cement types; mixing/curing water quality; admixtures;
      aggregates; curing; mass concrete; concrete production (mix design,
      trial mix, batching, mixing, transport, placing, compaction, slump,
      construction joints); nominal cover to reinforcement; sampling/testing
      frequency and acceptance of concrete.
  OUT: formwork; reinforcement steel (bars, fabrication, lapping, spacing -
      but a section about COVER to reinforcement is IN); surface finishes;
      administrative items (submittals, LEED/sustainability, references
      lists); site/project conditions.

Rules:
- Follow IN/OUT strictly: do NOT select formwork, reinforcement-steel,
  finishes, administrative or site-condition sections (except a cover
  sub-section as noted above).
- A parent heading has its OWN body text (the paragraphs before its first
  sub-heading), separate from its sub-sections. A broad parent such as a
  section titled just "Concrete" usually holds many in-scope requirements
  (mix design, batching, mixing, transport) in that own text - select it.
- When unsure whether a section is in scope, KEEP it.
- Selecting a section does NOT select its sub-sections or tables; list every
  id you want, including each relevant sub-section and table id.
- Generic headings (e.g. "General", "Quality Assurance", "Execution") may
  contain in-scope requirements; keep them unless clearly out of scope.
- Put each selected id in exactly one topic group:
{groups}

Return JSON with one id list per group (ids only, no headings):
{{"materials": ["S..."], "durability_grade": [...], "production_curing": [...], "cover_sampling": [...]}}

OUTLINE:
{outline}"""


EFFORT = "medium"


def main(out_dir=OUT_DIR):
    t0 = time.perf_counter()
    sections = read_json(out_dir / "sections.json")
    outline = (out_dir / "outline.txt").read_text(encoding="utf-8")
    groups_txt = "\n".join(f"  - {k}: {v}" for k, v in GROUPS.items())
    result, call = call_groq("localize", SYSTEM, PROMPT.format(groups=groups_txt, outline=outline),
                             expected_completion=2500, reasoning_effort=EFFORT)

    sec_by_id = {s["id"]: s for s in sections}
    tab_by_id = {t["id"]: (s, t) for s in sections for t in s["tables"]}
    picked, unknown = {}, []
    for grp in GROUPS:
        ids = (result or {}).get(grp) or []
        for iid in ids if isinstance(ids, list) else []:
            iid = str(iid).strip()
            if iid in sec_by_id or iid in tab_by_id:
                picked.setdefault(iid, grp)
            else:
                unknown.append(iid)

    # Deterministic safety net: when a sub-section was picked, its parent's
    # own body text (the lines before the first sub-heading) is often the
    # general part of the same topic, so keep it too.
    added_parents = []
    by_path = {tuple(s["heading_path"]): s for s in sections}
    for s in sections:
        if s["id"] in picked:
            parent = by_path.get(tuple(s["heading_path"][:-1]))
            if parent and parent["id"] not in picked and parent["text"].strip():
                picked[parent["id"]] = picked[s["id"]]
                added_parents.append(parent["id"])

    # A selected section already carries its tables; drop the table ids then.
    items = []
    for s in sections:
        if s["id"] in picked:
            items.append({"id": s["id"], "kind": "section", "group": picked[s["id"]],
                          "heading_path": s["heading_path"], "text": s["text"], "char_span": s["char_span"]})
        for t in s["tables"]:
            if t["id"] in picked and s["id"] not in picked:
                items.append({"id": t["id"], "kind": "table", "group": picked[t["id"]],
                              "heading_path": s["heading_path"] + [f"[TABLE] {t['caption'] or ''}".strip()],
                              "text": t["text"], "char_span": t["char_span"]})

    md_parts = []
    for it in items:
        if not it["text"].strip():
            continue
        md_parts.append(f"## [{it['id']}] {' > '.join(it['heading_path'])}\n\n{it['text']}\n")
    localized_md = "\n".join(md_parts)
    (out_dir / "localized.md").write_text(localized_md, encoding="utf-8")

    not_sel = []
    for s in sections:
        mark = "" if s["text"].strip() else "   (no body text)"
        if s["id"] not in picked:
            not_sel.append(f"{s['id']} {' > '.join(s['heading_path'])}{mark}")
        for t in s["tables"]:
            if t["id"] not in picked and s["id"] not in picked:
                not_sel.append(f"{t['id']} {' > '.join(s['heading_path'])} > [TABLE] {t['caption'] or '(no caption)'}")
    (out_dir / "not_selected.txt").write_text("\n".join(not_sel) + "\n", encoding="utf-8")

    out = {"call": call, "selected": [{k: v for k, v in it.items() if k != "text"} for it in items],
           "unknown_ids_returned": unknown, "parents_added_by_rule": added_parents,
           "raw_model_output": result}
    write_json(out_dir / "selected.json", out)
    n_sel_sections = sum(1 for it in items if it["kind"] == "section")
    print(f"[localize] picked {len(picked)} ids -> {n_sel_sections} sections + "
          f"{len(items) - n_sel_sections} standalone tables; {len(localized_md)} chars; "
          f"parents added by rule: {added_parents}; unknown ids: {unknown}")
    return {"wall_s": round(time.perf_counter() - t0, 2), "call": call, "n_items": len(items),
            "n_selected_sections": n_sel_sections, "n_sections": len(sections),
            "parents_added_by_rule": added_parents,
            "localized_chars": len(localized_md), "error": call["error"] or (None if result else "no JSON")}


if __name__ == "__main__":
    main()
