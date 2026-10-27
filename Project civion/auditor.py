"""Compliance engine: compares extracted values with the IS ground truth.

Pure Python, no LLM, no I/O. Every audited value is one entry in
database.PARAMETERS; the entry names its shape, and this file has one check
function per shape (CHECKS below). Adding a parameter therefore needs no code
here - see HOW_TO_ADD_PARAMETER.md.

Ledger statuses: Pass, Fail, Warning (value missing or unreadable),
Reference (the document points to another code / the drawings instead of
stating the value; counted as a pass).
"""
import math
import re

from database import IS383_2016, PARAMETERS


# ---------------------------------------------------------------------
# Reading values
# ---------------------------------------------------------------------
def is_missing(v):
    return v is None or v == "" or v == [] or v == {}


def to_number(v):
    """30 / "30 mins" / "M 30" -> 30.0; None if there is no number."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"\d+(?:\.\d+)?", str(v))
    return float(m.group()) if m else None


def to_range(v):
    """(low, high) from 30, [25, 35], {"min": 25, "max": 35}, "25-35" or "25 to 35"."""
    if isinstance(v, dict):
        v = [v.get("min"), v.get("max")]
    if isinstance(v, (list, tuple)):
        nums = [to_number(x) for x in v if to_number(x) is not None]
    else:
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v))] if not isinstance(v, bool) else []
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            nums = [float(v)]
    if not nums:
        raise ValueError(f"no number in {v!r}")
    return min(nums), max(nums)


def num(x):
    """Show 300.0 as 300 and 0.5 as 0.5."""
    return int(x) if float(x).is_integer() else x


def shown(r, unit=""):
    text = f"{num(r[0])}" if r[0] == r[1] else f"{num(r[0])} - {num(r[1])}"
    return f"{text} {unit}".strip()


def norm_key(s):
    """Key used to match table names: "600 micron" == "600 um", "Zone 2" == "zone II"."""
    s = str(s).lower().replace("µm", "um").replace("μm", "um")
    s = re.sub(r"microns?", "um", s)
    s = re.sub(r"zone\s*([1-4])\b", lambda m: "zone " + ["i", "ii", "iii", "iv"][int(m.group(1)) - 1], s)
    return re.sub(r"[\s_\-]+", "", s)


def apply_basis(value, spec):
    """Convert a value stated on another chemical basis to the limit's basis
    (e.g. "500 as SO4" -> 416.7 as SO3). Returns (value, note or None)."""
    basis = spec.get("basis")
    if not basis or not isinstance(value, str):
        return value, None
    text = value.upper().replace("₃", "3").replace("₄", "4").replace(" ", "")
    for name, factor in basis["convert"].items():
        if name.upper() in text:
            number = to_number(text.replace(name.upper(), ""))
            if number is None:
                return value, None
            converted = round(number * factor, 1)
            return converted, f"stated {value}; = {num(converted)} as {basis['limit_as']}"
    cleaned = text.replace(basis["limit_as"].upper(), "")
    return (to_number(cleaned) if to_number(cleaned) is not None else value), None


def grade_number(v):
    return to_number(str(v).upper().replace("M", " "))


# ---------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------
def resolve_limit(spec, ctx, is456_rules):
    """spec["limit"], or follow spec["limit_from"] into the IS tables."""
    if "limit" in spec:
        return spec["limit"]
    path = spec.get("limit_from")
    if not path:
        return None
    node = {"IS456": is456_rules, "IS383": IS383_2016}[path[0]]
    for key in path[1:]:
        key = key.format(**ctx) if "{" in key else key
        if not isinstance(node, dict) or key not in node:
            return spec.get("default")
        node = node[key]
    return node


def sulphate_class(get_val, is456_rules):
    """IS 456 Table 4 class from the site SO3 values (Class 1 if none given)."""
    try:
        soil = float(get_val('soil_total_so3_percent', 0) or 0)
        water = float(get_val('groundwater_so3_gl', 0) or 0)
        extract = float(get_val('soil_extract_2_1_so3_gl', 0) or 0)
    except (ValueError, TypeError):
        soil = water = extract = 0.0
    for t in is456_rules["SULPHATE_ATTACK_EXPOSURE"]["thresholds"]:
        if soil >= t["soil_so3"] or extract >= t["extract_so3"] or water >= t["water_so3"]:
            return t["class"]
    return "Class 1"


def adjust_durability(field, limit, ctx, is456_rules):
    """Table 5 limits raised by the sulphate class (Table 4) and freezing (cl 8.2.2)."""
    sc = ctx["sulphate_class"]
    classes = is456_rules["SULPHATE_ATTACK_EXPOSURE"]["classes"]
    if sc != "Class 1" and classes[sc]["cement_type"] != "Any":
        if field == "specified_min_cement":
            limit = max(limit, classes[sc]["min_cement"]["value"])
        if field == "specified_wc":
            limit = min(limit, classes[sc]["max_wc"])
    if field == "specified_grade" and ctx["freezing"]:
        freeze_grade = is456_rules["FREEZING_THAWING"]["min_grade"].get(ctx["concrete_type"])
        if freeze_grade and grade_number(freeze_grade) > grade_number(limit):
            limit = freeze_grade
    return limit


def is_samples(volume, rules):
    """Minimum number of samples for a quantity of concrete (IS 456 cl 15.2.2)."""
    for t in rules["thresholds"]:
        if volume <= t["max_m3"]:
            return t["samples"]
    # 4 plus one additional sample for each additional 50 m3 or part thereof
    return rules["base_50_samples"] + math.ceil((volume - 50) / rules["additional_step_m3"])


# ---------------------------------------------------------------------
# One check per shape: (value, limit, spec) -> (ok, shown value, requirement)
# ---------------------------------------------------------------------
def requirement_text(shape, limit, spec):
    """Requirement column for a row whose value is missing."""
    unit = spec.get("unit", "")
    if shape == "defined":
        return spec.get("requirement", "Must be defined")
    if limit is None or shape not in ("min", "max", "range", "equals", "not_in"):
        return f"Within {spec['clause']}"
    if shape == "min" and unit == "grade":
        return f"Min M{num(grade_number(limit))}"
    if shape == "min":
        return f"Min {num(limit)} {unit}".strip()
    if shape == "max":
        return f"Max {num(limit)} {unit}".strip()
    if shape == "range":
        return f"{num(limit[0])} - {num(limit[1])} {unit}".strip()
    if shape == "equals":
        return f"{num(limit)} {unit}".strip()
    return f"Not {' / '.join(limit)} (mechanical)"


def check_defined(value, limit, spec):
    return True, f"{value} {spec.get('unit', '')}".strip(), spec.get("requirement", "Must be defined")


def check_min(value, limit, spec):
    unit = spec.get("unit", "")
    if unit == "grade":
        r = to_range([grade_number(x) for x in (value if isinstance(value, list) else [value])])
        return r[0] >= grade_number(limit), str(value), f"Min M{num(grade_number(limit))}"
    r = to_range(value)
    return r[0] >= float(limit), shown(r, unit), f"Min {num(limit)} {unit}".strip()


def check_max(value, limit, spec):
    unit = spec.get("unit", "")
    r = to_range(value)
    return r[1] <= float(limit), shown(r, unit), f"Max {num(limit)} {unit}".strip()


def check_range(value, limit, spec):
    unit = spec.get("unit", "")
    r = to_range(value)
    lo, hi = limit
    return lo <= r[0] and r[1] <= hi, shown(r, unit), f"{num(lo)} - {num(hi)} {unit}".strip()


def check_equals(value, limit, spec):
    unit = spec.get("unit", "")
    v = to_number(value)
    if v is None:
        raise ValueError(f"no number in {value!r}")
    return v == float(limit), f"{num(v)} {unit}".strip(), f"{num(limit)} {unit}".strip()


def check_not_in(value, limit, spec):
    text = " ".join(map(str, value)) if isinstance(value, list) else str(value)
    ok = not any(word in text.lower() for word in limit)
    return ok, text, f"Not {' / '.join(limit)} (mechanical)"


def _compare_set(value, limit, compare):
    """Shared by set_max / set_range. Returns (n_checked, failures, unmatched)."""
    if not isinstance(value, dict):
        raise ValueError("expected {group: {item: value}}")
    groups = {norm_key(g): (g, items) for g, items in limit.items()}
    checked, failures, unmatched = 0, [], []
    for g_name, items in value.items():
        if norm_key(g_name) not in groups or not isinstance(items, dict):
            unmatched.append(str(g_name))
            continue
        is_name, is_items = groups[norm_key(g_name)]
        is_items = {norm_key(k): (k, v) for k, v in is_items.items()}
        for item, v in items.items():
            if is_missing(v) or to_number(v) is None:
                continue          # e.g. "--": the document sets no limit here
            if norm_key(item) not in is_items:
                unmatched.append(f"{g_name} / {item}")
                continue
            item_name, is_v = is_items[norm_key(item)]
            checked += 1
            ok, text = compare(to_range(v), is_v)
            if not ok:
                failures.append(f"{is_name} {item_name}: {text}")
    return checked, failures, unmatched


def _set_result(value, spec, checked, failures, unmatched):
    if checked == 0:
        raise ValueError("no stated item matches the IS table" +
                         (f" (unmatched: {', '.join(unmatched[:5])})" if unmatched else ""))
    shown_value = f"{checked} values in {len(value)} group(s)"
    req = f"Within {spec['clause']}"
    if failures:
        req += "; outside: " + "; ".join(failures[:6]) + (" ..." if len(failures) > 6 else "")
    if unmatched:
        req += f"; not in IS table: {', '.join(unmatched[:4])}"
    return not failures, shown_value, req


def check_set_max(value, limit, spec):
    checked, failures, unmatched = _compare_set(
        value, limit, lambda r, is_v: (r[1] <= is_v, f"{num(r[1])} > {num(is_v)}"))
    return _set_result(value, spec, checked, failures, unmatched)


def check_set_range(value, limit, spec):
    checked, failures, unmatched = _compare_set(
        value, limit, lambda r, is_v: (is_v[0] <= r[0] and r[1] <= is_v[1],
                                       f"{shown(r)} vs IS {num(is_v[0])}-{num(is_v[1])}"))
    return _set_result(value, spec, checked, failures, unmatched)


def check_sampling(value, rules, spec):
    """Bands like [{"from_m3": 5, "to_m3": 15, "samples": 2}, {"from_m3": 50, "to_m3": null,
    "samples": 4, "extra_per_m3": 50}]; each band must ask for at least the IS number."""
    if not isinstance(value, list) or not value:
        raise ValueError("expected a list of volume bands")
    failures = []
    for band in value:
        top, samples = band.get("to_m3"), to_number(band.get("samples"))
        if samples is None:
            continue
        if top is None:
            if samples < rules["base_50_samples"]:
                failures.append(f"above 50 m3: {num(samples)} < {rules['base_50_samples']}")
            step = to_number(band.get("extra_per_m3"))
            if step is not None and step > rules["additional_step_m3"]:
                failures.append(f"one extra per {num(step)} m3 > per {rules['additional_step_m3']} m3")
            continue
        need = is_samples(float(top), rules)
        if samples < need:
            failures.append(f"up to {num(float(top))} m3: {num(samples)} < {need}")
    req = "IS 456 cl 15.2.2 (1-5:1, 6-15:2, 16-30:3, 31-50:4, +1 per 50 m3)"
    if failures:
        req += "; short: " + "; ".join(failures)
    return not failures, f"{len(value)} bands", req


CHECKS = {
    "defined": check_defined, "min": check_min, "max": check_max, "range": check_range,
    "equals": check_equals, "not_in": check_not_in, "set_max": check_set_max,
    "set_range": check_set_range, "sampling": check_sampling,
}


# ---------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------
def run_civion_audit(user_data, is456_rules):
    def get_val(key, default=None):
        val = user_data.get(key)
        return val if val is not None else default

    def first(v):
        return (v[0] if v else None) if isinstance(v, list) else v

    c_type = first(get_val('concrete_type'))
    # Defaults kept from the previous auditor (see KNOWN_ISSUES.md #2).
    exposure = first(get_val('exposure', 'Moderate')) or 'Moderate'
    cem_type = first(get_val('cement_type', 'OPC')) or 'OPC'
    source_quotes = get_val('source_quotes', {}) or {}
    remarks = get_val('remarks', {}) or {}
    if not isinstance(remarks, dict):
        remarks = {}

    ctx = {"concrete_type": c_type, "exposure": exposure, "cement_type": cem_type,
           "sulphate_class": sulphate_class(get_val, is456_rules),
           "freezing": bool(get_val('freezing_thawing_exposure'))}

    # "reference" rows are also counted in "pass" (a reference is a valid way
    # to state a requirement); "reference" says how many of the passes they are.
    counts = {"pass": 0, "fail": 0, "warning": 0, "reference": 0, "total": 0}
    ledger = []
    traceability = []

    # References: the spec points elsewhere instead of stating a value, either
    # to another code ("grading per IS 383") or to a non-code source ("cover
    # as specified in the Drawings"). Each entry: {parameter, points_to,
    # source_quote}. "referenced_code" is the older key for points_to.
    references = {}
    raw_refs = get_val('cross_references', [])
    for ref in (raw_refs if isinstance(raw_refs, list) else []):
        if not isinstance(ref, dict):
            continue
        param = str(ref.get('parameter') or 'unknown_parameter').strip()
        points_to = ref.get('points_to') or ref.get('referenced_code') or 'Unknown source'
        quote = ref.get('source_quote') or 'No quote extracted'
        references.setdefault(param.lower(), {"parameter": param, "points_to": points_to,
                                              "source_quote": quote, "used": False})

    def find_reference(field):
        # "member_covers.Beams" is also covered by a reference for "member_covers".
        for key in (field.lower(), field.split('.')[0].lower()):
            if key in references:
                return references[key]
        return None

    def add_traceability(param, value):
        quote = source_quotes.get(param.split('.')[0], "No quote extracted")
        traceability.append({"Parameter": param, "Extracted Value": str(value), "Source Quote": quote})

    def add_row(metric, extracted, requirement, status, field=None, **extra):
        counts["total"] += 1
        counts[{"Pass": "pass", "Fail": "fail", "Warning": "warning", "Reference": "pass"}[status]] += 1
        if status == "Reference":
            counts["reference"] += 1
        row = {"Metric": metric, "Extracted Value": extracted, "Requirement": str(requirement),
               "Status": status, "Field": field}
        remark = remarks.get(field) or (remarks.get(field.split('.')[0]) if field else None)
        if remark:
            row["Remark"] = str(remark)
        row.update(extra)
        ledger.append(row)

    def add_missing(metric, requirement, field):
        # A value the spec does not state but points to elsewhere is a
        # REFERENCE, not MISSING.
        ref = find_reference(field) if field else None
        if ref:
            ref["used"] = True
            traceability.append({"Parameter": ref["parameter"], "Extracted Value": f"Refers to {ref['points_to']}",
                                 "Source Quote": ref["source_quote"]})
            add_row(metric, f"Refers to {ref['points_to']}", requirement, "Reference", field,
                    **{"Points To": ref["points_to"], "Source Quote": ref["source_quote"]})
        else:
            add_row(metric, "Not Provided", requirement, "Warning", field)

    def audit_one(field, spec):
        shape = spec["shape"]
        metric = spec["metric"]
        if shape == "cover":
            return audit_covers(field, spec)
        if shape == "strength_window":
            return audit_strength(field, spec)
        if shape == "sampling_count":
            return audit_sampling_count(field, spec)
        if shape == "sulphate_cement":
            return audit_sulphate_cement(field, spec)

        if shape == "sampling":
            limit = is456_rules["SAMPLING_FREQUENCY"]
        else:
            limit = resolve_limit(spec, ctx, is456_rules)
            if field in ("specified_grade", "specified_min_cement", "specified_wc"):
                limit = adjust_durability(field, limit, ctx, is456_rules)
        # exposure / cement type use the audit context (with its defaults).
        value = ctx[field] if field in ("exposure", "cement_type") else get_val(field)
        if is_missing(value):
            requirement = requirement_text(shape, limit, spec)
            if spec.get("basis"):
                requirement = f"{requirement} as {spec['basis']['limit_as']}"
            return add_missing(metric, requirement, field)
        add_traceability(field, value)
        value, basis_note = apply_basis(value, spec)
        try:
            ok, shown_value, requirement = CHECKS[shape](value, limit, spec)
        except (ValueError, TypeError, KeyError) as e:
            return add_row(metric, str(value), f"Could not read value ({e})", "Warning", field)
        if basis_note:
            shown_value = f"{shown_value} ({basis_note})"
        if spec.get("basis"):
            requirement = f"{requirement} as {spec['basis']['limit_as']}"
        add_row(metric, shown_value, requirement, "Pass" if ok else "Fail", field)

    # ---- single-use rules ------------------------------------------------
    def audit_covers(field, spec):
        fire = first(get_val('fire_resistance_rating', '1hr')) or '1hr'
        covers = get_val(field, {})
        if not isinstance(covers, dict):
            covers = {}
        if covers:
            add_traceability(field, covers)
        fire_table = is456_rules["FIRE_RESISTANCE_COVER"]["min_cover_mm"]
        durability_table = is456_rules["TABLE_16_NOMINAL_COVER"]["Reinforced_Concrete"]["Standard"]
        for member in ["Beams", "Columns", "Slabs"]:
            need = max(durability_table.get(exposure, 20), fire_table.get(member, {}).get(fire, 0))
            u_cov = covers.get(member)
            if is_missing(u_cov):
                add_missing(f"{member} Cover", f"Min {need}mm", f"{field}.{member}")
            else:
                v = to_number(u_cov)
                add_row(f"{member} Cover", f"{u_cov}mm", f"Min {need}mm",
                        "Pass" if v is not None and v >= need else "Fail", f"{field}.{member}")

    def audit_strength(field, spec):
        # Pre-existing check, kept unchanged (not a full IS 456 Table 11 check).
        u_grade = get_val('specified_grade')
        u_strength = get_val(field)
        u_sigma = get_val('specified_sigma')
        if u_grade and u_strength:
            add_traceability(field, u_strength)
            try:
                fck = int(str(u_grade).upper().replace("M", "").strip())
                sigma_dict = is456_rules["STANDARD_DEVIATION"]["assumed_sigma"]
                default_sigma = is456_rules["STANDARD_DEVIATION"]["default_sigma_high_grade"]
                sigma = float(u_sigma) if u_sigma else sigma_dict.get(str(u_grade).upper().strip(), default_sigma)
                tolerance = is456_rules["CHARACTERISTIC_STRENGTH"]["k_factor"] * sigma
                lower, upper = fck - tolerance, fck + tolerance
                ok = lower <= float(u_strength) <= upper
                add_row("Characteristic Strength", f"{u_strength} N/mm²", f"{lower:.1f} - {upper:.1f} N/mm²",
                        "Pass" if ok else "Fail", field)
            except Exception:
                add_row("Characteristic Strength", str(u_strength), "Valid Number Needed", "Warning", field)
        elif u_strength:
            add_row("Characteristic Strength", str(u_strength), "Needs Grade to verify", "Warning", field)
        else:
            add_missing("Characteristic Strength", "Expected value", field)

    def audit_sampling_count(field, spec):
        u_vol, u_samples = get_val('total_volume_m3'), get_val(field)
        if u_vol is None or u_samples is None:
            return add_missing("Sampling Sets", "Volume and Sets Required", field)
        add_traceability('total_volume_m3', u_vol)
        add_traceability(field, u_samples)
        need = is_samples(float(u_vol), is456_rules["SAMPLING_FREQUENCY"])
        add_row("Sampling Sets", str(u_samples), f"Req {need}",
                "Pass" if float(u_samples) >= need else "Fail", field)

    def audit_sulphate_cement(field, spec):
        sc = ctx["sulphate_class"]
        reqs = is456_rules["SULPHATE_ATTACK_EXPOSURE"]["classes"][sc]
        if sc != "Class 1" and reqs["cement_type"] != "Any":
            if cem_type:
                ok = cem_type in reqs["cement_type"]
                add_row("Sulfate Cement Type", cem_type, f"Req {reqs['cement_type']}",
                        "Pass" if ok else "Warning", "cement_type")
            else:
                add_row("Sulfate Cement Type", "Not Provided", f"Req {reqs['cement_type']}", "Warning", "cement_type")
        else:
            add_row("Sulfate Cement Type", cem_type or "Not Provided", "Class 1 / Any", "Pass", "cement_type")

    def add_reference_only_rows():
        # References that did not replace a missing row (e.g. "water shall be
        # tested per IS 3025") get a row of their own, unless the spec also
        # states a value for that parameter (the value is audited).
        for ref in references.values():
            if ref["used"]:
                continue
            base, _, sub = ref["parameter"].partition('.')
            value = get_val(base)
            if sub and isinstance(value, dict):
                value = value.get(sub)
            if not is_missing(value):
                traceability.append({"Parameter": ref["parameter"], "Extracted Value": f"Refers to {ref['points_to']}",
                                     "Source Quote": ref["source_quote"]})
                continue
            ref["used"] = True
            traceability.append({"Parameter": ref["parameter"], "Extracted Value": f"Refers to {ref['points_to']}",
                                 "Source Quote": ref["source_quote"]})
            add_row(f"{ref['parameter'].replace('_', ' ').title()} (Reference)", f"Refers to {ref['points_to']}",
                    f"As per {ref['points_to']}", "Reference", ref["parameter"],
                    **{"Points To": ref["points_to"], "Source Quote": ref["source_quote"]})

    def evaluate(metric, extracted, requirement, status_bool, is_warning=False, field=None):
        # Used only by the formwork checks below (kept as they were).
        if status_bool:
            add_row(metric, str(extracted), requirement, "Pass", field)
        elif extracted == "Not Provided":
            add_missing(metric, requirement, field)
        else:
            add_row(metric, str(extracted), requirement, "Warning" if is_warning else "Fail", field)

    try:
        for field, spec in PARAMETERS.items():
            try:
                audit_one(field, spec)
            except Exception as e:   # one bad value must not stop the audit
                add_row(spec["metric"], str(get_val(field)), f"Could not check ({e})", "Warning", field)
        formwork_checks(get_val, is456_rules, evaluate, add_traceability)
        add_reference_only_rows()
    except Exception as e:
        import traceback
        traceback.print_exc()
        ledger.append({"Metric": "System Error", "Extracted Value": "Error", "Requirement": "N/A", "Status": f"Warning: {str(e)}"})

    pct = round(100 * counts["pass"] / counts["total"]) if counts["total"] else 0
    summary = f"{pct}% passed, of which {counts['reference']} are references"
    return {"counts": counts, "summary": summary, "ledger": ledger, "traceability": traceability}


def formwork_checks(get_val, is456_rules, evaluate, add_traceability):
    """Formwork / shoring striking time (IS 456:2000 Clause 11.3). Unchanged from the previous auditor."""
    formwork_rules = is456_rules["CONSTRUCTION_PROCEDURES"]["Formwork_Striking_Time"]["min_period"]

    u_fw_hours = get_val('formwork_removal_hours', {})
    if not isinstance(u_fw_hours, dict):
        u_fw_hours = {}
    u_fw_days = get_val('formwork_removal_days', {})
    if not isinstance(u_fw_days, dict):
        u_fw_days = {}
    u_fw_span = get_val('formwork_span_m', {})
    if not isinstance(u_fw_span, dict):
        u_fw_span = {}

    u_wall_hours = u_fw_hours.get('Walls_Columns')
    req_wall_hours = formwork_rules["Walls_Columns_Vertical_Faces"]["min_hours"]
    if u_wall_hours is not None:
        add_traceability('formwork_removal_hours.Walls_Columns', u_wall_hours)
        evaluate("Formwork Removal - Walls/Columns", f"{u_wall_hours} hrs", f"Min {req_wall_hours} hrs", float(u_wall_hours) >= req_wall_hours)
    else:
        evaluate("Formwork Removal - Walls/Columns", "Not Provided", f"Min {req_wall_hours} hrs", False, True)

    u_slab_days = u_fw_days.get('Slabs')
    req_slab_days = formwork_rules["Slabs_Props_Left_Under"]["days"]
    if u_slab_days is not None:
        add_traceability('formwork_removal_days.Slabs', u_slab_days)
        evaluate("Formwork Removal - Slabs (props left under)", f"{u_slab_days} days", f"Min {req_slab_days} days", float(u_slab_days) >= req_slab_days)
    else:
        evaluate("Formwork Removal - Slabs (props left under)", "Not Provided", f"Min {req_slab_days} days", False, True)

    u_beam_soffit_days = u_fw_days.get('Beam_Soffit')
    req_beam_soffit_days = formwork_rules["Beam_Soffit_Props_Left_Under"]["days"]
    if u_beam_soffit_days is not None:
        add_traceability('formwork_removal_days.Beam_Soffit', u_beam_soffit_days)
        evaluate("Formwork Removal - Beam Soffit (props left under)", f"{u_beam_soffit_days} days", f"Min {req_beam_soffit_days} days", float(u_beam_soffit_days) >= req_beam_soffit_days)
    else:
        evaluate("Formwork Removal - Beam Soffit (props left under)", "Not Provided", f"Min {req_beam_soffit_days} days", False, True)

    u_props_slab_days = u_fw_days.get('Props_Under_Slabs')
    u_props_slab_span = u_fw_span.get('Props_Under_Slabs')
    if u_props_slab_days is not None and u_props_slab_span is not None:
        slab_key = "span_over_4.5m_days" if float(u_props_slab_span) > 4.5 else "span_up_to_4.5m_days"
        req_props_slab_days = formwork_rules["Props_Under_Slabs"][slab_key]
        add_traceability('formwork_removal_days.Props_Under_Slabs', u_props_slab_days)
        add_traceability('formwork_span_m.Props_Under_Slabs', u_props_slab_span)
        evaluate("Formwork Removal - Props Under Slabs", f"{u_props_slab_days} days (span {u_props_slab_span}m)", f"Min {req_props_slab_days} days", float(u_props_slab_days) >= req_props_slab_days)
    else:
        evaluate("Formwork Removal - Props Under Slabs", "Not Provided", "Depends on span", False, True)

    u_props_beam_days = u_fw_days.get('Props_Under_Beams_Arches')
    u_props_beam_span = u_fw_span.get('Props_Under_Beams_Arches')
    if u_props_beam_days is not None and u_props_beam_span is not None:
        beam_key = "span_over_6m_days" if float(u_props_beam_span) > 6 else "span_up_to_6m_days"
        req_props_beam_days = formwork_rules["Props_Under_Beams_Arches"][beam_key]
        add_traceability('formwork_removal_days.Props_Under_Beams_Arches', u_props_beam_days)
        add_traceability('formwork_span_m.Props_Under_Beams_Arches', u_props_beam_span)
        evaluate("Formwork Removal - Props Under Beams/Arches", f"{u_props_beam_days} days (span {u_props_beam_span}m)", f"Min {req_props_beam_days} days", float(u_props_beam_days) >= req_props_beam_days)
    else:
        evaluate("Formwork Removal - Props Under Beams/Arches", "Not Provided", "Depends on span", False, True)
