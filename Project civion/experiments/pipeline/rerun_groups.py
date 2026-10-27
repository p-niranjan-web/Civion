"""Re-run extraction for selected groups on an existing run's units/routing
(no Stage A / routing calls), then the quote check. Used to test prompt
changes on one group cheaply.

Usage: python rerun_groups.py --from-run run2 --out table_quotes_check durability materials
"""
import argparse
import shutil

from common import HERE, read_json, write_json
import extract_v2
import verify


def main(from_run, out, group_ids, exposure, concrete_type, max_call_tokens=5000, completion_reserve=1200):
    src, dst = HERE / "output_v2" / from_run, HERE / "output_v2" / out
    (dst / "extract_calls").mkdir(parents=True, exist_ok=True)
    for f in ["clean.md", "units.json", "routing.json"]:
        shutil.copy(src / f, dst / f)
    units = read_json(dst / "units.json")
    routing = read_json(dst / "routing.json")["routing"]
    extraction, quotes = {}, {}
    for gid in group_ids:
        g_units = [u for u in units if gid in routing.get(u["id"], [])]
        results, _ = extract_v2.extract_group(gid, g_units, dst, exposure, concrete_type,
                                              max_call_tokens, completion_reserve)
        values, q, _, _, _ = extract_v2.merge_group(gid, results)
        extraction.update(values)
        quotes.update(q)
    extraction["source_quotes"] = quotes
    write_json(dst / "extraction.json", extraction)
    clean_md = (dst / "clean.md").read_text(encoding="utf-8")
    rows = verify.check_quotes(extraction, clean_md)
    write_json(dst / "quote_check.json", rows)
    for r in rows:
        print(("OK  " if r["found"] else "MISS"), r["field"], r.get("value"), r.get("value_in_row", ""),
              "|", str(r["quote"]).replace("\n", " \n ")[:160], "|", r.get("missing_fragments") or "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-run", default="run2")
    ap.add_argument("--out", default="rerun")
    ap.add_argument("--exposure", default="Moderate")
    ap.add_argument("--concrete-type", default="Reinforced Concrete")
    ap.add_argument("groups", nargs="+")
    a = ap.parse_args()
    main(a.from_run, a.out, a.groups, a.exposure, a.concrete_type)
