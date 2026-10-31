"""Hand-built inputs run straight through the auditor (no LLM, no PDF).

Run: python test_dummy_audit.py   - prints the full dummy ledger, then one
pass / fail / missing case per shape, then checks that database.py,
parser.py and experiments/pipeline/groups.py name the same parameters.
Exits non-zero if any case gives an unexpected status.
"""
import json
import re
import sys
from pathlib import Path

from auditor import run_civion_audit
from database import IS456_MASTER, PARAMETERS

dummy_json = {
  "exposure": "Moderate",
  "freezing_thawing_exposure": True,
  "water_ph": 7.0,
  "soil_total_so3_percent": 0.5,
  "soil_extract_2_1_so3_gl": 1.5,
  "groundwater_so3_gl": 1.0,
  "concrete_type": "Reinforced Concrete",
  "specified_grade": "M30",
  "cement_type": "OPC",
  "specified_min_cement": 320,
  "specified_max_cement": 400,
  "specified_wc": 0.45,
  "specified_characteristic_strength": 30,
  "specified_sigma": 5.0,
  "mixing_time_minutes": 3,
  "transport_time_minutes": 20,
  "compaction_method": "mechanical vibrator",
  "curing_days": 7,
  "specified_slump_mm": 100,
  "max_aggregate_size_mm": 20,
  "total_volume_m3": 100,
  "specified_sampling_sets": 5,
  "sampling_cube_size_mm": 150,
  "measured_chloride_content": 0.2,
  "measured_so3_percent": 2.0,
  "fire_resistance_rating": "1hr",
  "member_covers": {
    "Beams": 25,
    "Columns": 40,
    "Slabs": 20
  }
}

# Context shared by the shape cases: no sulphate, no freezing, so Table 5 applies as is.
BASE = {"exposure": "Moderate", "concrete_type": "Reinforced Concrete", "cement_type": "OPC"}

# (name, extra input, metric, expected status)
CASES = [
    # min (Table 5 lookup: Moderate RC min cement 300)
    ("min pass", {"specified_min_cement": 300}, "Min Cement Content", "Pass"),
    ("min fail", {"specified_min_cement": 290}, "Min Cement Content", "Fail"),
    ("min missing", {}, "Min Cement Content", "Warning"),
    ("min grade pass", {"specified_grade": "M25"}, "Concrete Grade", "Pass"),
    ("min grade fail", {"specified_grade": "M20"}, "Concrete Grade", "Fail"),
    ("min range judged by low end", {"water_ph": [5.5, 9]}, "Water pH", "Fail"),
    ("min range pass", {"water_ph": [6, 9]}, "Water pH", "Pass"),
    # max (Table 5: Moderate RC max w/c 0.50)
    ("max pass", {"specified_wc": 0.45}, "W/C Ratio", "Pass"),
    ("max fail", {"specified_wc": 0.55}, "W/C Ratio", "Fail"),
    ("max range judged by high end", {"specified_wc": [0.5, 0.52]}, "W/C Ratio", "Fail"),
    ("max lookup by concrete type", {"water_chlorides_mg_l": 1000}, "Water - Chlorides", "Fail"),
    ("max missing", {}, "Water - Sulphates", "Warning"),
    # basis conversion: IS 456 Table 1 limit is 400 mg/l as SO3; 500 as SO4 = 416.7 as SO3
    ("sulphates SO4 converted fail", {"water_sulphates_mg_l": "500 as SO4"}, "Water - Sulphates", "Fail"),
    ("sulphates SO4 converted pass", {"water_sulphates_mg_l": "450 mg/l as SO4"}, "Water - Sulphates", "Pass"),
    ("sulphates SO3 as stated", {"water_sulphates_mg_l": "400 as SO3"}, "Water - Sulphates", "Pass"),
    ("sulphates plain number", {"water_sulphates_mg_l": 500}, "Water - Sulphates", "Fail"),
    ("max unreadable", {"specified_wc": "as directed"}, "W/C Ratio", "Warning"),
    # range (IS 456 cl 7.1: 25-150 mm overall)
    ("range pass", {"specified_slump_mm": [25, 35]}, "Slump", "Pass"),
    ("range fail", {"specified_slump_mm": [100, 180]}, "Slump", "Fail"),
    ("range single value", {"specified_slump_mm": "75 mm"}, "Slump", "Pass"),
    ("range missing", {}, "Slump", "Warning"),
    # min with lookup by cement type (IS 456 cl 13.5.1: OPC 7, PPC/PSC 10 days)
    ("curing OPC 7 pass", {"curing_days": 7}, "Curing Days", "Pass"),
    ("curing PPC 7 fail", {"cement_type": "PPC", "curing_days": 7}, "Curing Days", "Fail"),
    ("curing PSC 10 pass", {"cement_type": "PSC", "curing_days": 10}, "Curing Days", "Pass"),
    # equals
    ("equals pass", {"sampling_cube_size_mm": 150}, "Cube Size", "Pass"),
    ("equals fail", {"sampling_cube_size_mm": 100}, "Cube Size", "Fail"),
    # not_in
    ("not_in pass", {"compaction_method": "mechanical vibrator"}, "Compaction Method", "Pass"),
    ("not_in fail", {"compaction_method": "hand ramming"}, "Compaction Method", "Fail"),
    # defined
    ("defined pass", {"transport_time_minutes": 30}, "Transportation Time", "Pass"),
    ("defined missing", {}, "Transportation Time", "Warning"),
    # set_max (IS 383 Table 2)
    ("set_max pass", {"aggregate_deleterious_limits": {"coarse crushed": {"clay lumps": 1.0, "total": 2.0}}},
     "Aggregate - Deleterious Materials", "Pass"),
    ("set_max fail", {"aggregate_deleterious_limits": {"coarse crushed": {"finer than 75 um": 3.0, "total": 5.0},
                                                       "fine uncrushed": {"coal and lignite": 1.0}}},
     "Aggregate - Deleterious Materials", "Fail"),
    ("set_max no match", {"aggregate_deleterious_limits": {"pebbles": {"mud": 1}}},
     "Aggregate - Deleterious Materials", "Warning"),
    ("set_max missing", {}, "Aggregate - Deleterious Materials", "Warning"),
    # set_range (IS 383 Tables 7, 9)
    ("set_range pass", {"coarse_aggregate_grading": {"graded 20 mm": {"40 mm": 100, "20 mm": [95, 100],
                                                                       "10 mm": [25, 55], "4.75 mm": "0 to 10"}}},
     "Coarse Aggregate Grading", "Pass"),
    ("set_range fail", {"coarse_aggregate_grading": {"graded 20 mm": {"20 mm": [85, 100]}}},
     "Coarse Aggregate Grading", "Fail"),
    ("set_range key spelling", {"fine_aggregate_grading": {"Zone 2": {"600 micron": [35, 59], "150 µm": [0, 10]}}},
     "Fine Aggregate Grading", "Pass"),
    ("set_range reference", {"cross_references": [{"parameter": "fine_aggregate_grading", "points_to": "IS 383",
                                                   "source_quote": "Grading of fine aggregate shall conform to IS 383."}]},
     "Fine Aggregate Grading", "Reference"),
    # sampling bands (IS 456 cl 15.2.2)
    ("sampling pass", {"sampling_frequency": [{"from_m3": 0, "to_m3": 5, "samples": 1},
                                              {"from_m3": 5, "to_m3": 15, "samples": 2},
                                              {"from_m3": 15, "to_m3": 30, "samples": 3},
                                              {"from_m3": 30, "to_m3": 50, "samples": 4},
                                              {"from_m3": 50, "to_m3": None, "samples": 4, "extra_per_m3": 50}]},
     "Sampling Frequency", "Pass"),
    ("sampling fail", {"sampling_frequency": [{"from_m3": 0, "to_m3": 15, "samples": 1},
                                              {"from_m3": 50, "to_m3": None, "samples": 4, "extra_per_m3": 100}]},
     "Sampling Frequency", "Fail"),
    ("sampling missing", {}, "Sampling Frequency", "Warning"),
    # sampling count: 100 m3 needs 4 + 1 = 5 samples
    ("sampling count pass", {"total_volume_m3": 100, "specified_sampling_sets": 5}, "Sampling Sets", "Pass"),
    ("sampling count fail", {"total_volume_m3": 101, "specified_sampling_sets": 5}, "Sampling Sets", "Fail"),
    # cover and the non-code reference
    ("cover reference", {"cross_references": [{"parameter": "member_covers", "points_to": "drawings",
                                               "source_quote": "Cover as specified in the Drawings."}]},
     "Beams Cover", "Reference"),
    ("cover fail", {"member_covers": {"Beams": 25}}, "Beams Cover", "Fail"),
]


def row_for(result, metric):
    return next((r for r in result["ledger"] if r["Metric"] == metric), None)


def run_cases():
    bad = 0
    for name, extra, metric, expected in CASES:
        res = run_civion_audit({**BASE, **extra}, IS456_MASTER)
        row = row_for(res, metric)
        got = row["Status"] if row else "no row"
        ok = got == expected
        bad += not ok
        print(f"{'ok  ' if ok else 'BAD '} {name:32} {metric:34} expected {expected:9} got {got:9} | "
              f"{row['Extracted Value'] if row else ''} | {row['Requirement'] if row else ''}")
    return bad


def check_remark():
    res = run_civion_audit({**BASE, "specified_wc": 0.55, "remarks": {"specified_wc": "Clause 3.6 says 0.5 to 0.52."}},
                           IS456_MASTER)
    ok = row_for(res, "W/C Ratio").get("Remark") == "Clause 3.6 says 0.5 to 0.52."
    print(f"{'ok  ' if ok else 'BAD '} remark is copied onto the ledger row")
    return not ok


def check_sync():
    """database.PARAMETERS (extracted ones) and the extraction prompt (extraction_prompt.py) agree.

    The prompt module checks this itself when imported; the system prompt must also name every field."""
    problems = []
    try:
        import extraction_prompt
        system = extraction_prompt.build_system("Moderate", "Reinforced Concrete")
        extracted = {f for f, s in PARAMETERS.items() if s.get("from") not in ("user", "derived")}
        missing = sorted(f for f in extracted if f'"{f}":' not in system)
        if missing:
            problems.append(f"fields not in the prompt: {missing}")
    except RuntimeError as e:
        problems.append(str(e))
    print(("ok   schema sync" if not problems else "BAD  schema sync: " + "; ".join(problems)))
    return len(problems)


if __name__ == "__main__":
    res = run_civion_audit(dummy_json, IS456_MASTER)
    print(f"Total checks: {res['counts']['total']}  counts {res['counts']}  ({res['summary']})")
    for item in res['ledger']:
        print(f"  {item['Status']:9} {item['Metric']} | {item['Extracted Value']} | {item['Requirement']}")
    print()
    failures = run_cases() + check_remark() + check_sync()
    print(f"\n{len(CASES) + 2 - failures} of {len(CASES) + 2} checks as expected")
    sys.exit(1 if failures else 0)
