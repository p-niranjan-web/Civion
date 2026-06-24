import json
from auditor import run_civion_audit
from database import IS456_MASTER

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

res = run_civion_audit(dummy_json, IS456_MASTER)
print(f"Total checks: {res['counts']['total']}")
for item in res['ledger']:
    print(item['Metric'])

