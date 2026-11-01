"""Order in which the audit rows are shown (dashboard matrix, ledger, traceability, PDF reports).

Presentation only: the audit engine itself is unchanged. Rows are sorted by rank; rows that are
not listed keep the audit's own order between the "top" and the "lower" blocks.
"""

# ledger["Metric"] names, in the order they should appear
LEDGER_TOP = [
    "Concrete Type", "Environmental Exposure", "Cement Type",
    "Concrete Grade", "Min Cement Content", "Max Cement Content", "W/C Ratio",
    "Curing Days", "Water pH", "Water - Organic Solids", "Water - Inorganic Solids",
    "Water - Sulphates", "Water - Chlorides", "Water - Suspended Matter", "Chloride Content",
]
LEDGER_LOWER = ["Standard Deviation (sigma)", "Characteristic Strength"]
LEDGER_BOTTOM = [
    "Soil Total SO3", "Soil Extract SO3", "Groundwater SO3", "Sulfate Cement Type",
    "Freezing and Thawing", "Sulphate (SO3) Content",
]

# traceability["Parameter"] names (extraction field names), same idea
TRACE_TOP = [
    "concrete_type", "exposure", "cement_type", "specified_grade", "specified_min_cement",
    "specified_max_cement", "specified_wc", "curing_days", "water_ph", "water_organic_mg_l",
    "water_inorganic_mg_l", "water_sulphates_mg_l", "water_chlorides_mg_l",
    "water_suspended_matter_mg_l", "measured_chloride_content",
]
TRACE_LOWER = ["specified_sigma", "specified_characteristic_strength"]
TRACE_BOTTOM = [
    "soil_total_so3_percent", "soil_extract_2_1_so3_gl", "groundwater_so3_gl",
    "freezing_thawing_exposure", "measured_so3_percent",
]

MIDDLE = 100


def _ranker(top, lower, bottom):
    ranks = {}
    ranks.update({n: i for i, n in enumerate(top)})
    ranks.update({n: 200 + i for i, n in enumerate(lower)})
    ranks.update({n: 300 + i for i, n in enumerate(bottom)})
    return lambda name: ranks.get(name, MIDDLE)


_ledger_rank = _ranker(LEDGER_TOP, LEDGER_LOWER, LEDGER_BOTTOM)
_trace_rank = _ranker(TRACE_TOP, TRACE_LOWER, TRACE_BOTTOM)


def order_ledger(rows):
    return sorted(rows, key=lambda r: _ledger_rank(r.get("Metric")))      # stable


def order_audit(audit_results):
    """Sort audit_results["ledger"] and ["traceability"] in place and return it."""
    if isinstance(audit_results.get("ledger"), list):
        audit_results["ledger"] = order_ledger(audit_results["ledger"])
    if isinstance(audit_results.get("traceability"), list):
        audit_results["traceability"] = sorted(audit_results["traceability"],
                                               key=lambda r: _trace_rank(r.get("Parameter")))
    return audit_results
