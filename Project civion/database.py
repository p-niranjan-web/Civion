# -*- coding: utf-8 -*-
"""MASTER IS 456 PYTHON FILE - IMMUTABLE CONFIGURATION"""

IS456_MASTER = {
    # MVP 3
    "TABLE_5_DURABILITY": {
        "clause": "IS 456:2000 Table 5",
        "Plain Concrete": {
            "Mild": {"min_grade": "M10", "min_cement": 220, "max_wc": 0.60},
            "Moderate": {"min_grade": "M15", "min_cement": 240, "max_wc": 0.60},
            "Severe": {"min_grade": "M20", "min_cement": 250, "max_wc": 0.50},
            "Very Severe": {"min_grade": "M20", "min_cement": 260, "max_wc": 0.45},
            "Extreme": {"min_grade": "M25", "min_cement": 280, "max_wc": 0.40}
        },
        "Reinforced Concrete": {
            "Mild": {"min_grade": "M20", "min_cement": 300, "max_wc": 0.55},
            "Moderate": {"min_grade": "M25", "min_cement": 300, "max_wc": 0.50},
            "Severe": {"min_grade": "M30", "min_cement": 320, "max_wc": 0.45},
            "Very Severe": {"min_grade": "M35", "min_cement": 340, "max_wc": 0.45},
            "Extreme": {"min_grade": "M40", "min_cement": 360, "max_wc": 0.40}
        }
    },
    "CONSTRUCTION_PROCEDURES": {
        "Mixing": {
            "clause": "IS 456:2000 Clause 10.3",
            "min_time_mins": 2,
            "required_method": "mechanical",
        },
        "Transportation": {
            "clause": "IS 456:2000 Clause 13.1",
            "note": "Transport 'as rapidly as possible'; IS 456 gives no time limit"
        },
        "Compaction": {
            "clause": "IS 456:2000 Clause 13.3",
            "required_method": "mechanical vibrator",
            "prohibited": ["manual", "hand", "ramming"]
        },
        "Curing": {
            "clause": "IS 456:2000 Clause 13.5",
            "Plain Concrete": {"OPC": 7, "Mineral_Admixtures": 10, "Dry_Hot_Weather": 10},
            "Reinforced Concrete": {"OPC": 7, "Mineral_Admixtures": 10, "Dry_Hot_Weather": 14}
        },
        "Formwork_Striking_Time": {
            "clause": "IS 456:2000 Clause 11.3",
            "strength_condition": "Concrete must reach 2x the stress to which it may be subjected at the time of formwork removal",
            "min_period": {
                "Walls_Columns_Vertical_Faces": {"min_hours": 16, "max_hours": 24},
                "Slabs_Props_Left_Under": {"days": 3},
                "Beam_Soffit_Props_Left_Under": {"days": 7},
                "Props_Under_Slabs": {"span_up_to_4.5m_days": 7, "span_over_4.5m_days": 14},
                "Props_Under_Beams_Arches": {"span_up_to_6m_days": 14, "span_over_6m_days": 21}
            }
        }
    },
    "MATERIAL_PROPERTIES": {
        "Cement_Limits": {"clause": "IS 456:2000 Clause 8.2.4.2", "max_content": 450},
        "Water": {"clause": "IS 456:2000 Clause 5.4", "min_ph": 6.0},
        "Water_Solids_Limits": {
            "clause": "IS 456:2000 Clause 5.4, Table 1",
            "limits_mg_l": {
                "organic": 200,
                "inorganic": 3000,
                "sulphates_as_so4": 400,
                "chlorides": {"Plain Concrete": 2000, "Reinforced Concrete": 500},
                "suspended_matter": 2000
            }
        },
        "Sampling_Standard": {
            "clause": "IS 456:2000 Clause 15 / IS 516",
            "cube_size_mm": 150
        }
    },
    "TABLE_16_NOMINAL_COVER": {
        "clause": "IS 456:2000 Clause 12.3.2 & Table 16",
        "Reinforced_Concrete": {
            "Standard": {"Mild": 20, "Moderate": 30, "Severe": 45, "Very Severe": 50, "Extreme": 75},
            "Tolerance_Allowed": 10
        }
    },
    "WORKABILITY": {
        # IS 456 cl 7.1 table: slump (mm) by placing condition. "Very low" (blinding,
        # shallow sections, pavers) and "very high" (tremie) are not given as slump.
        "clause": "IS 456:2000 Clause 7.1",
        "categories": [
            {
                "degree": "Low",
                "keywords": ["mass concrete", "lightly reinforced", "floors", "hand placed pavements",
                             "canal lining", "strip footings"],
                "slump_min": 25, "slump_max": 75
            },
            {
                "degree": "Medium",
                "keywords": ["heavily reinforced"],
                "slump_min": 50, "slump_max": 100
            },
            {
                "degree": "Medium",
                "keywords": ["slipform", "pumped concrete"],
                "slump_min": 75, "slump_max": 100
            },
            {
                "degree": "High",
                "keywords": ["trench fill", "in-situ piling"],
                "slump_min": 100, "slump_max": 150
            }
        ],
        # Placing condition is usually unknown, so the audit uses the full span of the table.
        "overall_slump_mm": [25, 150]
    },
    "CHLORIDE_LIMITS": {
        "clause": "IS 456:2000 Table 7 (Page 21)",
        "max_chloride_kg_m3": {
            "Reinforced Concrete": 0.6,
            "Prestressed Concrete": 0.4,
            "Plain Concrete": 3.0
        }
    },
    "SULPHATE_LIMITS": {
        "reference": "IS 456:2000 Clause 8.2.4.1 (Page 20)",
        "max_water_soluble_so3_percent": 4.0,

    },
    "SULPHATE_ATTACK_EXPOSURE": {
        "clause": "IS 456:2000 Table 4 (Page 19)",
        "thresholds": [
            {"class": "Class 5", "soil_so3": 2.0, "extract_so3": 5.0, "water_so3": 5.0},
            {"class": "Class 4", "soil_so3": 1.0, "extract_so3": 3.1, "water_so3": 2.5},
            {"class": "Class 3", "soil_so3": 0.5, "extract_so3": 1.9, "water_so3": 1.2},
            {"class": "Class 2", "soil_so3": 0.2, "extract_so3": 1.0, "water_so3": 0.3},
            {"class": "Class 1", "soil_so3": 0.0, "extract_so3": 0.0, "water_so3": 0.0}
        ],
        "classes": {
            "Class 1": {"min_cement": {"value": 280, "unit": "kg/m3"}, "max_wc": 0.50, "cement_type": "Any"},
            "Class 2": {"min_cement": {"value": 310, "unit": "kg/m3"}, "max_wc": 0.50, "cement_type": "SRC/PPC/PSC"},
            "Class 3": {"min_cement": {"value": 330, "unit": "kg/m3"}, "max_wc": 0.50, "cement_type": "SRC/PPC/PSC"},
            "Class 4": {"min_cement": {"value": 350, "unit": "kg/m3"}, "max_wc": 0.45, "cement_type": "SRC"},
            "Class 5": {"min_cement": {"value": 370, "unit": "kg/m3"}, "max_wc": 0.45, "cement_type": "SRC+Coating"}
        }
    },
    "STANDARD_DEVIATION": {
        "clause": "IS 456:2000 Table 8 (Page 23)",
        "assumed_sigma": {
            "M10": 3.5, "M15": 3.5,
            "M20": 4.0, "M25": 4.0,
            "M30": 5.0, "M35": 5.0, "M40": 5.0, "M45": 5.0, "M50": 5.0,
            "M55": 5.0, "M60": 6.0
        },
        "default_sigma_high_grade": 6.0
    },
    "CHARACTERISTIC_STRENGTH": {
        "clause": "IS 456:2000 Table 11 (Page 30)",
        "k_factor": 0.825,
        "logic": "Acceptance limit = fck ± (k * sigma)"
    },
    "FREEZING_THAWING": {
        "reference": "IS 456:2000 Clause 8.2.2 (Page 18)",
        "min_grade": {"Plain Concrete": "M20", "Reinforced Concrete": "M25"},
        "logic": "Concrete exposed to freezing and thawing shall have entrained air. Min grade M20 for PCC and M25 for RCC."
    },
    "SAMPLING_FREQUENCY": {
        "clause": "IS 456:2000 Clause 15.2.2 (Page 29)",
        "thresholds": [
            {"max_m3": 5, "samples": 1},
            {"max_m3": 15, "samples": 2},
            {"max_m3": 30, "samples": 3},
            {"max_m3": 50, "samples": 4}
        ],
        "base_50_samples": 4,
        "additional_step_m3": 50,
        "additional_sample_increment": 1
    },
    "FIRE_RESISTANCE_COVER": {
        "clause": "IS 456:2000 Table 16A (Page 47)",
        "min_cover_mm": {
            "Beams": {"0.5hr": 20, "1hr": 20, "1.5hr": 20, "2hr": 40, "4hr": 60},
            "Columns": {"0.5hr": 40, "1hr": 40, "1.5hr": 40, "2hr": 40, "4hr": 40},
            "Slabs": {"0.5hr": 20, "1hr": 20, "1.5hr": 25, "2hr": 35, "4hr": 45}
        }
    }
}

# A user's spec document can legitimately defer a parameter to another IS code
# instead of stating a number itself (e.g. "aggregate grading shall conform to
# IS 383"). That is not missing data - it's a valid cross-reference. This dict
# holds the correct reference values for each external code the parser/auditor
# knows how to recognize, so the chatbot can answer with real numbers instead
# of guessing from the LLM's own training knowledge. Keyed by the code string
# the parser is asked to detect in `cross_references[].referenced_code`.
EXTERNAL_CODE_REFERENCES = {
    "IS 383": {
        "title": "IS 383:2016 - Coarse and Fine Aggregates for Concrete - Specification",
        "topic": "Grading limits for single-sized coarse aggregate (nominal size 20 mm), Table 7",
        "grading_limits_20mm_percent_passing": {
            "40.0mm": "100",
            "20.0mm": "85-100",
            "10.0mm": "0-20",
            "4.75mm": "0-5"
        }
    }
}


# =====================================================================
# IS 383:2016 (Coarse and fine aggregate for concrete), values checked
# against the code text. Ranges are [min, max] percent passing.
# Designation and sieve names here are the names the extraction must use.
# =====================================================================
IS383_2016 = {
    "TABLE_2_DELETERIOUS": {
        "clause": "IS 383:2016 Clause 5.2.1, Table 2",
        # percent by mass, max. A material with no entry has no limit in that column.
        "limits": {
            "fine uncrushed":      {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 3.00,
                                    "shale": 1.00, "total": 5.00},
            "fine crushed":        {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 15.00,
                                    "total": 2.00},
            "fine mixed":          {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 12.00,
                                    "total": 2.00},
            "fine manufactured":   {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 10.00,
                                    "shale": 1.00, "total": 2.00},
            "coarse uncrushed":    {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 1.00,
                                    "soft fragments": 3.00, "total": 5.00},
            "coarse crushed":      {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 1.00,
                                    "total": 2.00},
            "coarse manufactured": {"coal and lignite": 1.00, "clay lumps": 1.00, "finer than 75 um": 1.00,
                                    "soft fragments": 3.00, "total": 2.00},
        },
    },
    "TABLE_7_COARSE_GRADING": {
        "clause": "IS 383:2016 Clauses 6.1 and 6.2, Table 7",
        "limits": {
            "single-sized 63 mm":   {"80 mm": [100, 100], "63 mm": [85, 100], "40 mm": [0, 30], "20 mm": [0, 5],
                                     "10 mm": [0, 5]},
            "single-sized 40 mm":   {"63 mm": [100, 100], "40 mm": [85, 100], "20 mm": [0, 20], "10 mm": [0, 5]},
            "single-sized 20 mm":   {"40 mm": [100, 100], "20 mm": [85, 100], "10 mm": [0, 20], "4.75 mm": [0, 5]},
            "single-sized 16 mm":   {"20 mm": [100, 100], "16 mm": [85, 100], "10 mm": [0, 30], "4.75 mm": [0, 5]},
            "single-sized 12.5 mm": {"16 mm": [100, 100], "12.5 mm": [85, 100], "10 mm": [0, 45], "4.75 mm": [0, 10]},
            "single-sized 10 mm":   {"12.5 mm": [100, 100], "10 mm": [85, 100], "4.75 mm": [0, 20], "2.36 mm": [0, 5]},
            "graded 40 mm":         {"80 mm": [100, 100], "40 mm": [90, 100], "20 mm": [30, 70], "10 mm": [10, 35],
                                     "4.75 mm": [0, 5]},
            "graded 20 mm":         {"40 mm": [100, 100], "20 mm": [90, 100], "10 mm": [25, 55], "4.75 mm": [0, 10]},
            "graded 16 mm":         {"20 mm": [100, 100], "16 mm": [90, 100], "10 mm": [30, 70], "4.75 mm": [0, 10]},
            "graded 12.5 mm":       {"20 mm": [100, 100], "12.5 mm": [90, 100], "10 mm": [40, 85], "4.75 mm": [0, 10]},
        },
    },
    "TABLE_9_FINE_GRADING": {
        "clause": "IS 383:2016 Clause 6.3, Table 9",
        # Note 1 (crushed stone sand: 150 um up to 20 %) and the 5 % allowance of cl 6.3 apply to
        # test results of an actual sand, not to the limits a specification states; not used here.
        "limits": {
            "zone I":   {"10 mm": [100, 100], "4.75 mm": [90, 100], "2.36 mm": [60, 95], "1.18 mm": [30, 70],
                         "600 um": [15, 34], "300 um": [5, 20], "150 um": [0, 10]},
            "zone II":  {"10 mm": [100, 100], "4.75 mm": [90, 100], "2.36 mm": [75, 100], "1.18 mm": [55, 90],
                         "600 um": [35, 59], "300 um": [8, 30], "150 um": [0, 10]},
            "zone III": {"10 mm": [100, 100], "4.75 mm": [90, 100], "2.36 mm": [85, 100], "1.18 mm": [75, 100],
                         "600 um": [60, 79], "300 um": [12, 40], "150 um": [0, 10]},
            "zone IV":  {"10 mm": [100, 100], "4.75 mm": [95, 100], "2.36 mm": [95, 100], "1.18 mm": [90, 100],
                         "600 um": [80, 100], "300 um": [15, 50], "150 um": [0, 15]},
        },
    },
    "TABLE_10_ALL_IN_GRADING": {
        "clause": "IS 383:2016 Clause 6.4, Table 10",
        "limits": {
            "40 mm": {"80 mm": [100, 100], "40 mm": [95, 100], "20 mm": [45, 75], "4.75 mm": [25, 45],
                      "600 um": [8, 30], "150 um": [0, 6]},
            "20 mm": {"40 mm": [100, 100], "20 mm": [95, 100], "4.75 mm": [30, 50], "600 um": [10, 35],
                      "150 um": [0, 6]},
        },
    },
}


# =====================================================================
# PARAMETERS - one entry per audited value, in ledger order.
#
# Key = field name in the extraction JSON (parser.py schema and
# experiments/pipeline/groups.py use the same name).
#   metric     - ledger row name
#   shape      - which comparison auditor.py runs (see SHAPES)
#   unit       - shown next to values
#   clause     - IS clause the limit comes from
#   limit      - the IS value, OR
#   limit_from - where to read it: ["IS456" or "IS383", key, key, ...];
#                "{concrete_type}", "{exposure}", "{cement_type}" are filled
#                in from the audit context (exposure is chosen by the user)
#   default    - limit used when limit_from finds nothing (unknown type etc.)
#   from       - "user" (chosen in the UI, not extracted) or "derived" (computed
#                by the auditor); absent = extracted from the document
#
# Any parameter the document does not state but points to another code or
# to the drawings becomes a REFERENCE row (auditor.py, for every shape).
# =====================================================================
SHAPES = {
    "defined":   "Only has to be stated; IS gives no number to compare.",
    "min":       "value >= limit. A stated range is judged by its lower end.",
    "max":       "value <= limit. A stated range is judged by its upper end.",
    "range":     "value (or both ends of a stated range) inside [low, high].",
    "equals":    "value == limit.",
    "not_in":    "text must not contain any word of the limit list.",
    "set_max":   "{group: {item: value}}: every item IS also lists must be <= the IS value.",
    "set_range": "{group: {item: [low, high]}}: every stated range must lie inside the IS range.",
    "sampling":  "volume bands [{from_m3, to_m3, samples, extra_per_m3}]: each band >= IS sampling rule.",
    # Single-use rules (one parameter each; too specific for a general shape):
    "cover":           "member_covers: per member, max(Table 16 for exposure, Table 16A for fire rating).",
    "strength_window": "characteristic strength vs grade +/- k*sigma (pre-existing check, unchanged).",
    "sampling_count":  "number of samples for a stated total volume (IS 456 cl 15.2.2).",
    "sulphate_cement": "cement type required by the sulphate class (IS 456 Table 4).",
}

PARAMETERS = {
    # ---- context and site (exposure and concrete type come from the user) ----
    "concrete_type": {"metric": "Concrete Type", "shape": "defined", "from": "user", "clause": "IS 456:2000 Table 5"},
    "exposure": {"metric": "Environmental Exposure", "shape": "defined", "from": "user", "clause": "IS 456:2000 Table 3"},
    "cement_type": {"metric": "Cement Type", "shape": "defined", "clause": "IS 456:2000 Clause 5.1"},
    "soil_total_so3_percent": {"metric": "Soil Total SO3", "shape": "defined", "unit": "%", "requirement": "Limit depends on class",
                               "clause": "IS 456:2000 Table 4"},
    "soil_extract_2_1_so3_gl": {"metric": "Soil Extract SO3", "shape": "defined", "unit": "g/l", "requirement": "Limit depends on class",
                                "clause": "IS 456:2000 Table 4"},
    "groundwater_so3_gl": {"metric": "Groundwater SO3", "shape": "defined", "unit": "g/l", "requirement": "Limit depends on class",
                           "clause": "IS 456:2000 Table 4"},
    "sulphate_cement": {"metric": "Sulfate Cement Type", "shape": "sulphate_cement", "from": "derived",
                        "clause": "IS 456:2000 Table 4"},
    "freezing_thawing_exposure": {"metric": "Freezing and Thawing", "shape": "defined", "requirement": "Defined",
                                  "clause": "IS 456:2000 Clause 8.2.2"},

    # ---- grade, strength, durability (Table 5 limits may be raised by Table 4 / cl 8.2.2) ----
    "specified_grade": {"metric": "Concrete Grade", "shape": "min", "unit": "grade",
                        "clause": "IS 456:2000 Table 5",
                        "limit_from": ["IS456", "TABLE_5_DURABILITY", "{concrete_type}", "{exposure}", "min_grade"],
                        "default": "M20"},
    "specified_min_cement": {"metric": "Min Cement Content", "shape": "min", "unit": "kg/m³",
                             "clause": "IS 456:2000 Table 5",
                             "limit_from": ["IS456", "TABLE_5_DURABILITY", "{concrete_type}", "{exposure}", "min_cement"],
                             "default": 300},
    "specified_max_cement": {"metric": "Max Cement Content", "shape": "max", "unit": "kg/m³",
                             "clause": "IS 456:2000 Clause 8.2.4.2",
                             "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Cement_Limits", "max_content"]},
    "specified_wc": {"metric": "W/C Ratio", "shape": "max",
                     "clause": "IS 456:2000 Table 5",
                     "limit_from": ["IS456", "TABLE_5_DURABILITY", "{concrete_type}", "{exposure}", "max_wc"],
                     "default": 0.55},
    "specified_sigma": {"metric": "Standard Deviation (sigma)", "shape": "defined", "unit": "N/mm²", "requirement": "Based on Grade",
                        "clause": "IS 456:2000 Table 8"},
    "specified_characteristic_strength": {"metric": "Characteristic Strength", "shape": "strength_window",
                                          "unit": "N/mm²", "clause": "IS 456:2000 Table 11"},

    # ---- cover ----
    "fire_resistance_rating": {"metric": "Fire Resistance Rating", "shape": "defined", "requirement": "Required for cover",
                               "clause": "IS 456:2000 Table 16A"},
    "member_covers": {"metric": "Cover", "shape": "cover", "unit": "mm",
                      "clause": "IS 456:2000 Table 16 and Table 16A"},

    # ---- production ----
    "mixing_time_minutes": {"metric": "Mixing Time", "shape": "min", "unit": "mins",
                            "clause": "IS 456:2000 Clause 10.3.1",
                            "limit_from": ["IS456", "CONSTRUCTION_PROCEDURES", "Mixing", "min_time_mins"]},
    "transport_time_minutes": {"metric": "Transportation Time", "shape": "defined", "unit": "mins", "requirement": "Stated (IS 456 cl 13.1 sets no time limit)",
                               "clause": "IS 456:2000 Clause 13.1 (sets no time limit)"},
    "compaction_method": {"metric": "Compaction Method", "shape": "not_in",
                          "clause": "IS 456:2000 Clause 13.3",
                          "limit_from": ["IS456", "CONSTRUCTION_PROCEDURES", "Compaction", "prohibited"]},
    "curing_days": {"metric": "Curing Days", "shape": "min", "unit": "days",
                    "clause": "IS 456:2000 Clause 13.5.1",
                    "limit_from": ["IS456", "CONSTRUCTION_PROCEDURES", "Curing", "{concrete_type}", "{cement_type}"],
                    "default": 7},
    "specified_slump_mm": {"metric": "Slump", "shape": "range", "unit": "mm",
                           "clause": "IS 456:2000 Clause 7.1",
                           "limit_from": ["IS456", "WORKABILITY", "overall_slump_mm"]},

    # ---- water (IS 456 cl 5.4, Table 1) ----
    "water_ph": {"metric": "Water pH", "shape": "min", "clause": "IS 456:2000 Clause 5.4",
                 "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water", "min_ph"]},
    "water_organic_mg_l": {"metric": "Water - Organic Solids", "shape": "max", "unit": "mg/l",
                           "clause": "IS 456:2000 Clause 5.4, Table 1",
                           "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water_Solids_Limits", "limits_mg_l", "organic"]},
    "water_inorganic_mg_l": {"metric": "Water - Inorganic Solids", "shape": "max", "unit": "mg/l",
                             "clause": "IS 456:2000 Clause 5.4, Table 1",
                             "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water_Solids_Limits", "limits_mg_l", "inorganic"]},
    "water_sulphates_mg_l": {"metric": "Water - Sulphates", "shape": "max", "unit": "mg/l",
                             "clause": "IS 456:2000 Clause 5.4, Table 1",
                             "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water_Solids_Limits", "limits_mg_l", "sulphates_as_so4"]},
    "water_chlorides_mg_l": {"metric": "Water - Chlorides", "shape": "max", "unit": "mg/l",
                             "clause": "IS 456:2000 Clause 5.4, Table 1",
                             "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water_Solids_Limits", "limits_mg_l", "chlorides", "{concrete_type}"],
                             "default": 500},
    "water_suspended_matter_mg_l": {"metric": "Water - Suspended Matter", "shape": "max", "unit": "mg/l",
                                    "clause": "IS 456:2000 Clause 5.4, Table 1",
                                    "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Water_Solids_Limits", "limits_mg_l", "suspended_matter"]},

    # ---- chemical limits of the concrete ----
    "measured_chloride_content": {"metric": "Chloride Content", "shape": "max", "unit": "kg/m³",
                                  "clause": "IS 456:2000 Table 7",
                                  "limit_from": ["IS456", "CHLORIDE_LIMITS", "max_chloride_kg_m3", "{concrete_type}"],
                                  "default": 0.6},
    "measured_so3_percent": {"metric": "Sulphate (SO3) Content", "shape": "max", "unit": "%",
                             "clause": "IS 456:2000 Clause 8.2.4.1",
                             "limit_from": ["IS456", "SULPHATE_LIMITS", "max_water_soluble_so3_percent"]},

    # ---- aggregates (IS 383:2016) ----
    "aggregate_deleterious_limits": {"metric": "Aggregate - Deleterious Materials", "shape": "set_max", "unit": "%",
                                     "clause": "IS 383:2016 Table 2",
                                     "limit_from": ["IS383", "TABLE_2_DELETERIOUS", "limits"]},
    "coarse_aggregate_grading": {"metric": "Coarse Aggregate Grading", "shape": "set_range", "unit": "% passing",
                                 "clause": "IS 383:2016 Table 7",
                                 "limit_from": ["IS383", "TABLE_7_COARSE_GRADING", "limits"]},
    "fine_aggregate_grading": {"metric": "Fine Aggregate Grading", "shape": "set_range", "unit": "% passing",
                               "clause": "IS 383:2016 Table 9",
                               "limit_from": ["IS383", "TABLE_9_FINE_GRADING", "limits"]},
    "all_in_aggregate_grading": {"metric": "All-in Aggregate Grading", "shape": "set_range", "unit": "% passing",
                                 "clause": "IS 383:2016 Table 10",
                                 "limit_from": ["IS383", "TABLE_10_ALL_IN_GRADING", "limits"]},

    # ---- sampling ----
    "total_volume_m3": {"metric": "Total Volume", "shape": "defined", "unit": "m³", "requirement": "Required for sampling",
                        "clause": "IS 456:2000 Clause 15.2.2"},
    "sampling_cube_size_mm": {"metric": "Cube Size", "shape": "equals", "unit": "mm",
                              "clause": "IS 456:2000 Clause 15 / IS 516",
                              "limit_from": ["IS456", "MATERIAL_PROPERTIES", "Sampling_Standard", "cube_size_mm"]},
    "specified_sampling_sets": {"metric": "Sampling Sets", "shape": "sampling_count",
                                "clause": "IS 456:2000 Clause 15.2.2"},
    "sampling_frequency": {"metric": "Sampling Frequency", "shape": "sampling",
                           "clause": "IS 456:2000 Clause 15.2.2"},
}
