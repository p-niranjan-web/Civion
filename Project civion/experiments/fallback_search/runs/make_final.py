"""Round 2: build keywords.json from runs/keywords_r1.json. Change ids match changes.md."""
import json

k = json.load(open("runs/keywords_r1.json", encoding="utf-8"))
k["_note"] = k["_note"].replace("round-1 edits per changes.md.", "round-1 and round-2 edits per changes.md (final).")
P = k["parameters"]
# D3 max cement: only maximum-qualified phrasings
P["specified_max_cement"]["terms"] = [
    "maximum cement content", "max cement content", "maximum cementitious content",
    "maximum cementitious material content", "maximum binder content",
    r"re:cement(itious)?( material)? content[^.|]{0,60}(shall not exceed|not to exceed|not exceeding|not more than|should not exceed)",
    r"re:(maximum|max\.?|upper limit)( of)?[^.|]{0,20}cement(itious)?( material)? content",
]
# D4 transport: drop bare placed/placing
tt = P["transport_time_minutes"]["terms"]
for t in ("placed", "placing", "placed in position"):
    tt.remove(t)
tt += ["placed in position within", "deposited within"]
# D5 water solids vs aggregate deleterious materials
for n in ("water_organic_mg_l", "water_inorganic_mg_l", "water_sulphates_mg_l",
          "water_chlorides_mg_l", "water_suspended_matter_mg_l"):
    P[n]["exclude"] += ["aggregate", "aggregates"]
P["water_organic_mg_l"]["terms"].remove("organic impurities")
# D6 water sulphates vs sulphate-resisting cement
P["water_sulphates_mg_l"]["exclude"] += ["sulphate resisting", "sulfate resisting"]
# D7 water chlorides vs admixture chloride limits
P["water_chlorides_mg_l"]["exclude"] += ["admixture", "admixtures", "calcium chloride"]
# D8 compaction vs surface finishing
P["compaction_method"]["exclude"] += ["laitance"]

json.dump(k, open("keywords.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
