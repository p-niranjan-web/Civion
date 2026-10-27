"""Round 1: build keywords_r1.json from keywords_v0.json. Change ids match changes.md."""
import json

k = json.load(open("keywords_v0.json", encoding="utf-8"))
k["_note"] = k["_note"].replace("BEFORE opening the BLR document.",
                                "BEFORE opening the BLR document; round-1 edits per changes.md.")
M = k["hint_macros"]
# C1 superscript flattening: 'm 3', 'mm 2'
M["@kg_m3"] = r"kg\s*/\s*(m\s*3|m\^3|cum|cu\.?\s*m|cubic\s*m)|kg\s*per\s*(m\s*3|cum|cu\.?\s*m|cubic)"
M["@volume"] = r"(?<![/\d])\b\d[\d,]*(\.\d+)?\s*(m\s*3\b|cum\b|cu\.?\s*m\b|cubic\s*met)"
# C3 reference lines
ge = k["global_exclude"]
ge["code_line_regex"] = r"^\W*((\d+|[a-z])[.)]\s*)?(is|bs|bs en|en|astm|aci|irc|sp|crsi|aashto)\s*[:\-]?\s*\d"
ge["title_line_regex"] = (r"^\W*(specification for|specifications for|code of practice|method of test|"
                          r"methods of test|methods of testing|guide for|standard practice for|recommended practice)")
# C11 cross-reference hint
k["cross_ref_regex"] = (
    r"\b(as|be)\s+(specified|shown|indicated|detailed|given|stipulated|designated|listed)\s+(in|on|by)\s+(the\s+)?(drawings?|tables?|is\b|clause)"
    r"|\bstipulated in\b"
    r"|\b(conform(s|ing)?|comply|complying|in accordance)\s+(to|with)\s+(the\s+requirements\s+(of|in)\s+)?is\s*:?\s*\d"
    r"|\btables?\s*-*\s*\d+\s*(herein|of is|below|above)"
    r"|\bas per (the )?(drawings?|is\s*\d|tables?)")
P = k["parameters"]
for n, p in P.items():
    if not p["descriptive"] and n != "total_volume_m3":
        p["cross_ref"] = True
# C4 cement terms
P["cement_type"]["terms"] += ["sulphate resistance", "sulfate resistance", "sulphate resistant", "sulfate resistant",
                              "low heat", "moderate heat", "super sulphated", "supersulphated", "rapid hardening", "white cement"]
# C5 compaction false hits
P["compaction_method"]["exclude"] += ["fully compacted", "compacting factor", "compacting type screeds"]
# C6 curing false hits
P["curing_days"]["exclude"] += ["days prior", "days in advance", "grout"]
# C7 transport synonyms
P["transport_time_minutes"]["terms"] += ["placed in position", "from the time", "after mixing", "of mixing",
                                         "placed", "placing", "time of production", "after batching"]
# C8 total volume: sampling-frequency tables
P["total_volume_m3"]["exclude_context"] = ["number of samples", "sampling", "frequency", "samples"]
# C9 cube size adjacency + cm
P["sampling_cube_size_mm"]["terms"] += ["molds", "mold", "moulds"]
P["sampling_cube_size_mm"]["value_hints"] = [
    r"\b\d+(\.\d+)?\s*(mm|cm)\s*(\w+\s+){0,2}(cubes?|cylinders?|moulds?|molds?|specimens?)\b",
    r"\b(cubes?|cylinders?|moulds?|molds?|specimens?)\s+(of\s+)?(size\s+)?\d+(\.\d+)?\s*(mm|cm)\b",
    r"\b\d+\s*x\s*\d+"]
# C10 spelled-out counts
P["specified_sampling_sets"]["value_hints"].append(
    r"\b(one|two|three|four|five|six)\s+(additional\s+)?(samples?|sets?|cubes?|specimens?)\b")
# C12 grade: steel and cement grades
P["specified_grade"]["exclude"] += ["fe", "33 grade", "43 grade", "53 grade"]

json.dump(k, open("runs/keywords_r1.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
