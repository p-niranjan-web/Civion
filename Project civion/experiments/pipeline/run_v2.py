"""v2 runner: clean -> sections -> Stage A (localize.py, unchanged call) ->
scope expansion + units + Stage B routing (route.py) -> per-group extraction
(extract_v2.py) -> auditor.run_civion_audit -> deterministic quote check.

Every run writes to output_v2/<run-name>/ so runs can be compared.
Usage: python run_v2.py --run-name run1 [--exposure Moderate] [--concrete-type "Reinforced Concrete"]
       [--input path/to/docling.md]
"""
import argparse
import time

from common import CALL_LOG, HERE, write_json
import clean
import sections
import localize
import route
import extract_v2
import verify


def run(run_name, exposure, concrete_type, max_call_tokens, src=None):
    from auditor import run_civion_audit
    from database import IS456_MASTER

    out_dir = HERE / "output_v2" / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    CALL_LOG.clear()
    t_all = time.perf_counter()
    st = {}
    t = time.perf_counter(); st["clean"] = {**clean.main(src=src or clean.DEFAULT_IN, dst=out_dir / "clean.md"), "wall_s": round(time.perf_counter() - t, 3)}
    t = time.perf_counter(); st["sections"] = {**sections.main(out_dir=out_dir), "wall_s": round(time.perf_counter() - t, 3)}
    st["stage_a"] = localize.main(out_dir=out_dir)
    if st["stage_a"]["error"] or not st["stage_a"]["n_items"]:
        # Never continue on an empty scope (run1's first attempt did, silently).
        raise SystemExit(f"Stage A failed: {st['stage_a']['error'] or 'no ids selected'}")
    st["stage_b"] = route.main(out_dir=out_dir)
    extraction, info = extract_v2.main(out_dir, exposure, concrete_type, max_call_tokens)
    st["extract"] = info
    write_json(out_dir / "extraction.json", extraction)

    t = time.perf_counter()
    audit = run_civion_audit({k: v for k, v in extraction.items() if k != "conflicts"}, IS456_MASTER)
    st["audit"] = {"wall_s": round(time.perf_counter() - t, 3)}
    write_json(out_dir / "audit.json", audit)

    clean_md = (out_dir / "clean.md").read_text(encoding="utf-8")
    write_json(out_dir / "quote_check.json", verify.check_quotes(extraction, clean_md))
    write_json(out_dir / "run_stats.json", {
        "args": {"input": str(src or clean.DEFAULT_IN), "exposure": exposure, "concrete_type": concrete_type, "max_call_tokens": max_call_tokens},
        "steps": st, "calls": list(CALL_LOG), "total_wall_s": round(time.perf_counter() - t_all, 2)})
    print(f"[run_v2] {run_name} done in {time.perf_counter() - t_all:.1f}s; audit counts {audit['counts']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", default="run1")
    ap.add_argument("--exposure", default="Moderate")
    ap.add_argument("--concrete-type", default="Reinforced Concrete")
    ap.add_argument("--max-call-tokens", type=int, default=5000)
    ap.add_argument("--input", default=None, help="Docling markdown to audit (default: BLR)")
    a = ap.parse_args()
    run(a.run_name, a.exposure, a.concrete_type, a.max_call_tokens, a.input)
