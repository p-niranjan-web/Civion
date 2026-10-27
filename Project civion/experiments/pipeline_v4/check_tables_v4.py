"""Check every extracted aggregate-table cell of a BLR run against BLR's own markdown
tables (deterministic). Adapted copy of experiments/shapes/check_tables_blr.py, which
only reads pipeline/output_v2/<run>; this one takes "v2:<run>" or "v4:<run>" (v4 reads
pipeline_v4/output/<run>/doc.md). Column/row matching is by header text, written for
checking only - it is not part of the pipeline.
Usage (from pipeline_v4): python check_tables_v4.py v4:main1"""
import json, re, sys
from pathlib import Path
kind, run = sys.argv[1].split(":", 1)
HERE = Path(__file__).resolve().parent
d = (HERE.parent / "pipeline" / "output_v2" if kind == "v2" else HERE / "output") / run
ext = json.loads((d / "extraction.json").read_text(encoding="utf-8"))
md = (d / ("clean.md" if kind == "v2" else "doc.md")).read_text(encoding="utf-8").splitlines()

def tables():
    out, cur = [], None
    for l in md:
        if l.strip().startswith("|"):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if cur is None:
                cur = {"header": cells, "rows": []}; out.append(cur)
            elif not re.match(r"^[-:| ]+$", l.strip()):
                cur["rows"].append(cells)
        else:
            cur = None
    return out

def rng(s):
    n = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    return None if not n or s.strip() in ("--", "-", "") else (min(n), max(n))

def sieve(s):
    s = s.lower().replace("micron", "um").replace(" ", "")
    return s
T = tables()
def find(word):
    return next(t for t in T if word in " ".join(t["header"]).lower())

def check(field, table, colmap):
    v = ext.get(field) or {}
    ok = bad = 0; errs = []
    for g, items in v.items():
        if not isinstance(items, dict): continue
        col = colmap(g)
        if col is None: errs.append(f"no column for {g}"); continue
        for s, val in items.items():
            if val is None: continue
            row = next((r for r in table["rows"] if sieve(r[0]) == sieve(s)), None)
            doc = rng(row[col]) if row else None
            got = tuple(map(float, val)) if isinstance(val, list) else (float(val), float(val))
            if doc == got: ok += 1
            else: bad += 1; errs.append(f"{g} / {s}: extracted {val}, doc {row[col] if row else 'no row'}")
    # cells in the document that were not extracted
    print(f"{field}: {ok} cells match the document, {bad} do not")
    for e in errs[:12]: print("   ", e)

coarse = find("single - sized")
def ccol(g):
    m = re.match(r"(single-sized|graded) ([\d.]+) mm", g)
    kind = "single - sized" if m.group(1) == "single-sized" else "graded"
    for i, h in enumerate(coarse["header"]):
        if kind in h.lower() and h.strip().endswith(f"- {m.group(2)} mm"): return i
check("coarse_aggregate_grading", coarse, ccol)
fine = find("grading zone")
check("fine_aggregate_grading", fine, lambda g: next((i for i, h in enumerate(fine["header"]) if h.lower().endswith("zone " + g.split()[1].lower())), None))
allin = find("all in")
check("all_in_aggregate_grading", allin, lambda g: next((i for i, h in enumerate(allin["header"]) if f"- {g} nominal" in h.lower()), None))
dele = find("deleterious")
cols = {"fine uncrushed": 3, "fine crushed": 4, "coarse uncrushed": 5, "coarse crushed": 6}
items = {"coal and lignite": "coal", "clay lumps": "clay", "finer than 75 um": "finer", "soft fragments": "soft",
         "shale": "shale", "total": "total"}
ok = bad = 0
for g, its in (ext.get("aggregate_deleterious_limits") or {}).items():
    for it, val in (its or {}).items():
        if val is None: continue
        row = next(r for r in dele["rows"] if items[it] in r[1].lower())
        doc = rng(row[cols[g]]) if g in cols else None
        if doc and doc[1] == float(val): ok += 1
        else: bad += 1; print(f"    deleterious {g} / {it}: extracted {val}, doc {row[cols[g]] if g in cols else 'no such column'}")
print(f"aggregate_deleterious_limits: {ok} cells match, {bad} do not")
print("sampling_frequency:", json.dumps(ext.get("sampling_frequency")))
print("quote:", (ext.get("source_quotes") or {}).get("sampling_frequency"))
