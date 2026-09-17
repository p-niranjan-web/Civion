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
            "max_time_mins": 30
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
        "clause": "IS 456:2000 Page 17",
        "categories": [
            {
                "keywords": ["mass concrete", "lightly reinforced"],
                "slump_min": 25, "slump_max": 75
            },
            {
                "keywords": ["normal rcc"],
                "slump_min": 50, "slump_max": 100
            },
            {
                "keywords": ["pumped concrete", "heavily reinforced"],
                "slump_min": 100, "slump_max": 150
            }
        ]
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
