"""Score hit files against the hand labels in labels.json. Prints a metrics table
and writes runs/metrics.json. Every hit must already be labelled."""
import json

RUNS = {
    "v0": "runs/hits_v0_searchv0.json",             # keywords_v0 + search.py as first written
    "v0_kw_final_code": "runs/hits_v0_searchfinal.json",
    "r1": "runs/hits_r1.json",                        # round-1 keywords + round-1 code
    "final": "runs/hits_final.json",                  # keywords.json + final search.py
}
L = json.load(open("labels.json", encoding="utf-8"))
out = {}
for run, path in RUNS.items():
    hits = json.load(open(path, encoding="utf-8"))["hits"]
    out[run] = {}
    for p, hs in hits.items():
        labs = [L[p].get(str(h["line"])) for h in hs]
        assert None not in labs, (run, p, [h["line"] for h in hs if str(h["line"]) not in L[p]])
        r = labs.count("R")
        out[run][p] = {"hits": len(hs), "relevant": r, "irrelevant": len(hs) - r, "found": r > 0}
json.dump(out, open("runs/metrics.json", "w", encoding="utf-8"), indent=1)

print(f"{'parameter':36} " + "  ".join(f"{r:>18}" for r in RUNS))
for p in out["final"]:
    print(f"{p:36} " + "  ".join(f"{out[r][p]['hits']:>8} / {out[r][p]['relevant']:<7}" for r in RUNS))
for r in RUNS:
    tot_h = sum(v["hits"] for v in out[r].values())
    tot_r = sum(v["relevant"] for v in out[r].values())
    found = sum(v["found"] for v in out[r].values())
    print(f"{r}: hits={tot_h} relevant={tot_r} precision={tot_r / tot_h:.2f} params_found={found}/{len(out[r])}")
