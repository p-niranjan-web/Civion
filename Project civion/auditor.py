def run_civion_audit(user_data, is456_rules):
    def get_val(key, default=None):
        val = user_data.get(key)
        return val if val is not None else default

    c_type = get_val('concrete_type')
    if isinstance(c_type, list):
        c_type = c_type[0] if c_type else None
        
    exposure = get_val('exposure', 'Moderate')
    if isinstance(exposure, list):
        exposure = exposure[0] if exposure else 'Moderate'
        
    cem_type = get_val('cement_type', 'OPC')
    if isinstance(cem_type, list):
        cem_type = cem_type[0] if cem_type else 'OPC'
        
    source_quotes = get_val('source_quotes', {})
    if source_quotes is None:
        source_quotes = {}

    counts = {"pass": 0, "fail": 0, "warning": 0, "total": 0}
    ledger = []
    traceability = []
    
    def add_traceability(param, value):
        quote = source_quotes.get(param, "No quote extracted")
        traceability.append({"Parameter": param, "Extracted Value": str(value), "Source Quote": quote})

    def evaluate(metric, extracted, requirement, status_bool, is_warning=False):
        counts["total"] += 1
        if status_bool:
            status = "Pass"
            counts["pass"] += 1
        else:
            if is_warning:
                status = "Warning"
                counts["warning"] += 1
            else:
                status = "Fail"
                counts["fail"] += 1
                
        ledger.append({
            "Metric": metric,
            "Extracted Value": str(extracted) if extracted is not None else "Not Provided",
            "Requirement": str(requirement),
            "Status": status
        })

    # Record traceabilities for key values
    if c_type: add_traceability('concrete_type', c_type)
    if exposure: add_traceability('exposure', exposure)

    try:
        # =====================================================
        # SECTION 1 — STRUCTURAL SAFETY & STRENGTH
        # =====================================================
        
        # Explicitly evaluate base conditions
        if c_type is not None:
            evaluate("Concrete Type", c_type, "Must be defined", True)
        else:
            evaluate("Concrete Type", "Not Provided", "Must be defined", False, True)

        if exposure is not None:
            evaluate("Environmental Exposure", exposure, "Must be defined", True)
        else:
            evaluate("Environmental Exposure", "Not Provided", "Must be defined", False, True)

        if cem_type is not None:
            evaluate("Cement Type", cem_type, "Must be defined", True)
        else:
            evaluate("Cement Type", "Not Provided", "Must be defined", False, True)

        # Cascading Durability Limits (Table 5)
        if c_type in is456_rules["TABLE_5_DURABILITY"]:
            durability_rules = is456_rules["TABLE_5_DURABILITY"][c_type].get(exposure, {})
            req_min_grade = durability_rules.get("min_grade", "M20")
            req_min_cement = durability_rules.get("min_cement", 300)
            req_max_wc = durability_rules.get("max_wc", 0.55)
        else:
            req_min_grade = "M20"
            req_min_cement = 300
            req_max_wc = 0.55
        
        # Cascading with Sulfate Attack (Table 4)
        try:
            soil_so3 = float(get_val('soil_total_so3_percent', 0) or 0)
            water_so3 = float(get_val('groundwater_so3_gl', 0) or 0)
            extract_so3 = float(get_val('soil_extract_2_1_so3_gl', 0) or 0)
        except (ValueError, TypeError):
            soil_so3 = water_so3 = extract_so3 = 0.0
            
        u_soil_so3 = get_val('soil_total_so3_percent')
        if u_soil_so3 is not None:
            add_traceability('soil_total_so3_percent', u_soil_so3)
            evaluate("Soil Total SO3", f"{u_soil_so3}%", "Limit depends on class", True)
        else:
            evaluate("Soil Total SO3", "Not Provided", "Limit depends on class", False, True)

        u_ext_so3 = get_val('soil_extract_2_1_so3_gl')
        if u_ext_so3 is not None:
            add_traceability('soil_extract_2_1_so3_gl', u_ext_so3)
            evaluate("Soil Extract SO3", f"{u_ext_so3} g/l", "Limit depends on class", True)
        else:
            evaluate("Soil Extract SO3", "Not Provided", "Limit depends on class", False, True)

        u_gw_so3 = get_val('groundwater_so3_gl')
        if u_gw_so3 is not None:
            add_traceability('groundwater_so3_gl', u_gw_so3)
            evaluate("Groundwater SO3", f"{u_gw_so3} g/l", "Limit depends on class", True)
        else:
            evaluate("Groundwater SO3", "Not Provided", "Limit depends on class", False, True)
        
        sulfate_class = "Class 1"
        for thresh in is456_rules["SULPHATE_ATTACK_EXPOSURE"]["thresholds"]:
            if soil_so3 >= thresh["soil_so3"] or extract_so3 >= thresh["extract_so3"] or water_so3 >= thresh["water_so3"]:
                sulfate_class = thresh["class"]
                break
                
        if sulfate_class != "Class 1" and is456_rules["SULPHATE_ATTACK_EXPOSURE"]["classes"][sulfate_class]["cement_type"] != "Any":
            sulfate_reqs = is456_rules["SULPHATE_ATTACK_EXPOSURE"]["classes"][sulfate_class]
            req_min_cement = max(req_min_cement, sulfate_reqs["min_cement"]["value"])
            req_max_wc = min(req_max_wc, sulfate_reqs["max_wc"])
            if cem_type:
                evaluate("Sulfate Cement Type", cem_type, f"Req {sulfate_reqs['cement_type']}", cem_type in sulfate_reqs["cement_type"], is_warning=True)
            else:
                evaluate("Sulfate Cement Type", "Not Provided", f"Req {sulfate_reqs['cement_type']}", False, is_warning=True)
        else:
            evaluate("Sulfate Cement Type", cem_type or "Not Provided", "Class 1 / Any", True)
        
        # Cascading with Freezing and Thawing
        u_freeze = get_val('freezing_thawing_exposure')
        if u_freeze is not None:
            add_traceability('freezing_thawing_exposure', u_freeze)
            evaluate("Freezing and Thawing", str(u_freeze), "Defined", True)
            if u_freeze and c_type in is456_rules["FREEZING_THAWING"]["min_grade"]:
                freeze_min_grade = is456_rules["FREEZING_THAWING"]["min_grade"][c_type]
                if int(freeze_min_grade[1:]) > int(req_min_grade[1:]):
                    req_min_grade = freeze_min_grade
        else:
            evaluate("Freezing and Thawing", "Not Provided", "Defined", False, True)

        # Evaluate Grade
        u_grade = get_val('specified_grade')
        if u_grade:
            add_traceability('specified_grade', u_grade)
            try:
                user_fck = int(str(u_grade).upper().replace("M", "").strip())
                req_fck = int(req_min_grade.replace("M", "").strip())
                evaluate("Concrete Grade", u_grade, f"Min {req_min_grade}", user_fck >= req_fck)
            except ValueError:
                evaluate("Concrete Grade", u_grade, f"Min {req_min_grade}", False, True)
        else:
            evaluate("Concrete Grade", "Not Provided", f"Min {req_min_grade}", False, True)

        # Evaluate Min Cement
        u_cement = get_val('specified_min_cement')
        if u_cement:
            add_traceability('specified_min_cement', u_cement)
            evaluate("Min Cement Content", f"{u_cement} kg/m³", f"Min {req_min_cement} kg/m³", float(u_cement) >= req_min_cement)
        else:
            evaluate("Min Cement Content", "Not Provided", f"Min {req_min_cement} kg/m³", False, True)
            
        # Max Cement Content
        u_max_cem = get_val('specified_max_cement')
        if u_max_cem is not None:
            add_traceability('specified_max_cement', u_max_cem)
            evaluate("Max Cement Content", f"{u_max_cem} kg/m³", "Max 450 kg/m³", float(u_max_cem) <= 450)
        else:
            evaluate("Max Cement Content", "Not Provided", "Max 450 kg/m³", False, True)

        # Evaluate Max W/C Ratio
        u_wc = get_val('specified_wc')
        if u_wc:
            add_traceability('specified_wc', u_wc)
            evaluate("W/C Ratio", u_wc, f"Max {req_max_wc}", float(u_wc) <= req_max_wc)
        else:
            evaluate("W/C Ratio", "Not Provided", f"Max {req_max_wc}", False, True)

        # Evaluate Characteristic Strength
        u_strength = get_val('specified_characteristic_strength')
        u_sigma = get_val('specified_sigma')
        
        if u_sigma is not None:
            evaluate("Standard Deviation (sigma)", u_sigma, "Based on Grade", True)
        else:
            evaluate("Standard Deviation (sigma)", "Not Provided", "Based on Grade", False, True)
        
        if u_grade and u_strength:
            add_traceability('specified_characteristic_strength', u_strength)
            try:
                fck = int(str(u_grade).upper().replace("M", "").strip())
                sigma_dict = is456_rules["STANDARD_DEVIATION"]["assumed_sigma"]
                default_sigma = is456_rules["STANDARD_DEVIATION"]["default_sigma_high_grade"]
                
                if u_sigma:
                    sigma = float(u_sigma)
                else:
                    sigma = sigma_dict.get(str(u_grade).upper().strip(), default_sigma)
                    
                k = is456_rules["CHARACTERISTIC_STRENGTH"]["k_factor"]
                tolerance = k * sigma
                lower_limit = fck - tolerance
                upper_limit = fck + tolerance
                
                evaluate("Characteristic Strength", f"{u_strength} N/mm²", f"{lower_limit:.1f} - {upper_limit:.1f} N/mm²", lower_limit <= float(u_strength) <= upper_limit)
            except Exception as e:
                evaluate("Characteristic Strength", u_strength, "Valid Number Needed", False, True)
        elif u_strength:
            evaluate("Characteristic Strength", u_strength, "Needs Grade to verify", False, True)
        else:
            evaluate("Characteristic Strength", "Not Provided", "Expected value", False, True)

        # Evaluate Member Covers
        u_fire_time = get_val('fire_resistance_rating', '1hr')
        provided_fire = get_val('fire_resistance_rating')
        if provided_fire is not None:
            add_traceability('fire_resistance_rating', provided_fire)
            val_to_eval = provided_fire[0] if isinstance(provided_fire, list) else provided_fire
            evaluate("Fire Resistance Rating", val_to_eval, "Required for cover", True)
        else:
            evaluate("Fire Resistance Rating", "Not Provided", "Required for cover", False, True)
            
        if isinstance(u_fire_time, list): u_fire_time = u_fire_time[0] if u_fire_time else '1hr'
        u_member_covers = get_val('member_covers', {})
        if not isinstance(u_member_covers, dict):
            u_member_covers = {}
            
        if u_member_covers:
            add_traceability('member_covers', u_member_covers)
            
        fire_table = is456_rules["FIRE_RESISTANCE_COVER"]["min_cover_mm"]
        durability_table = is456_rules["TABLE_16_NOMINAL_COVER"]["Reinforced_Concrete"]["Standard"]
        
        for member in ["Beams", "Columns", "Slabs"]:
            u_cov = u_member_covers.get(member)
            dur_req = durability_table.get(exposure, 20)
            fire_req = fire_table.get(member, {}).get(u_fire_time, 0)
            absolute_min = max(dur_req, fire_req)
            if u_cov is not None:
                evaluate(f"{member} Cover", f"{u_cov}mm", f"Min {absolute_min}mm", float(u_cov) >= absolute_min)
            else:
                evaluate(f"{member} Cover", "Not Provided", f"Min {absolute_min}mm", False, True)

        # =====================================================
        # SECTION 2 — CONSTRUCTION & WORKABILITY
        # =====================================================
        mix_time = get_val("mixing_time_minutes")
        req_mix = is456_rules["CONSTRUCTION_PROCEDURES"]["Mixing"]["min_time_mins"]
        if mix_time:
            add_traceability('mixing_time_minutes', mix_time)
            evaluate("Mixing Time", f"{mix_time} mins", f"Min {req_mix} mins", float(mix_time) >= req_mix)
        else:
            evaluate("Mixing Time", "Not Provided", f"Min {req_mix} mins", False, True)

        u_trans = get_val('transport_time_minutes')
        if u_trans is not None:
            add_traceability('transport_time_minutes', u_trans)
            evaluate("Transportation Time", f"{u_trans} mins", "Max 30 mins", float(u_trans) <= 30)
        else:
            evaluate("Transportation Time", "Not Provided", "Max 30 mins", False, True)

        comp_method = get_val("compaction_method", "")
        if isinstance(comp_method, list): comp_method = comp_method[0] if comp_method else ""
        comp_method = str(comp_method).lower()
        if comp_method:
            add_traceability('compaction_method', comp_method)
            prohibited = is456_rules["CONSTRUCTION_PROCEDURES"]["Compaction"]["prohibited"]
            status = not any(p in comp_method for p in prohibited)
            evaluate("Compaction Method", comp_method, "Mechanical Vibrator", status)
        else:
            evaluate("Compaction Method", "Not Provided", "Mechanical Vibrator", False, True)

        curing_days = get_val("curing_days")
        req_curing = 7
        if c_type in is456_rules["CONSTRUCTION_PROCEDURES"]["Curing"]:
            req_curing = is456_rules["CONSTRUCTION_PROCEDURES"]["Curing"][c_type].get(cem_type, 7)
            
        if curing_days:
            add_traceability('curing_days', curing_days)
            evaluate("Curing Days", f"{curing_days} days", f"Min {req_curing} days", float(curing_days) >= req_curing)
        else:
            evaluate("Curing Days", "Not Provided", f"Min {req_curing} days", False, True)
            
        u_slump = get_val('specified_slump_mm')
        if u_slump is not None:
            add_traceability('specified_slump_mm', u_slump)
            evaluate("Slump", f"{u_slump}mm", "25 - 150mm", 25 <= float(u_slump) <= 150)
        else:
            evaluate("Slump", "Not Provided", "25 - 150mm", False, True)

        # Formwork / Shoring Striking Time (IS 456:2000 Clause 11.3)
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

        # =====================================================
        # SECTION 3 — MATERIALS & CHEMICAL LIMITS
        # =====================================================

        # Cross-references to other IS codes (e.g. "aggregate grading shall
        # conform to IS 383"): the spec correctly defers the number to another
        # code instead of stating it, so this counts as satisfied rather than
        # missing data.
        cross_references = get_val('cross_references', [])
        if isinstance(cross_references, list):
            for ref in cross_references:
                if not isinstance(ref, dict):
                    continue
                param = ref.get('parameter', 'Unknown Parameter')
                code = ref.get('referenced_code', 'Unknown Code')
                quote = ref.get('source_quote', 'No quote extracted')
                traceability.append({"Parameter": param, "Extracted Value": f"Deferred to {code}", "Source Quote": quote})
                evaluate(f"{param.replace('_', ' ').title()} (Cross-Reference)", f"Deferred to {code}", f"Compliant per {code}", True)

        u_ph = get_val('water_ph')
        if u_ph is not None:
            add_traceability('water_ph', u_ph)
            evaluate("Water pH", u_ph, "Min 6.0", float(u_ph) >= 6.0)
        else:
            evaluate("Water pH", "Not Provided", "Min 6.0", False, True)

        # Permissible Limits for Solids in Water (IS 456:2000 Clause 5.4, Table 1)
        water_solids_limits = is456_rules["MATERIAL_PROPERTIES"]["Water_Solids_Limits"]["limits_mg_l"]

        u_water_organic = get_val('water_organic_mg_l')
        limit_organic = water_solids_limits["organic"]
        if u_water_organic is not None:
            add_traceability('water_organic_mg_l', u_water_organic)
            evaluate("Water - Organic Solids", f"{u_water_organic} mg/l", f"Max {limit_organic} mg/l", float(u_water_organic) <= limit_organic)
        else:
            evaluate("Water - Organic Solids", "Not Provided", f"Max {limit_organic} mg/l", False, True)

        u_water_inorganic = get_val('water_inorganic_mg_l')
        limit_inorganic = water_solids_limits["inorganic"]
        if u_water_inorganic is not None:
            add_traceability('water_inorganic_mg_l', u_water_inorganic)
            evaluate("Water - Inorganic Solids", f"{u_water_inorganic} mg/l", f"Max {limit_inorganic} mg/l", float(u_water_inorganic) <= limit_inorganic)
        else:
            evaluate("Water - Inorganic Solids", "Not Provided", f"Max {limit_inorganic} mg/l", False, True)

        u_water_sulphates = get_val('water_sulphates_mg_l')
        limit_sulphates = water_solids_limits["sulphates_as_so4"]
        if u_water_sulphates is not None:
            add_traceability('water_sulphates_mg_l', u_water_sulphates)
            evaluate("Water - Sulphates", f"{u_water_sulphates} mg/l", f"Max {limit_sulphates} mg/l", float(u_water_sulphates) <= limit_sulphates)
        else:
            evaluate("Water - Sulphates", "Not Provided", f"Max {limit_sulphates} mg/l", False, True)

        u_water_chlorides = get_val('water_chlorides_mg_l')
        limit_chlorides = water_solids_limits["chlorides"].get(c_type, water_solids_limits["chlorides"]["Reinforced Concrete"])
        if u_water_chlorides is not None:
            add_traceability('water_chlorides_mg_l', u_water_chlorides)
            evaluate("Water - Chlorides", f"{u_water_chlorides} mg/l", f"Max {limit_chlorides} mg/l", float(u_water_chlorides) <= limit_chlorides)
        else:
            evaluate("Water - Chlorides", "Not Provided", f"Max {limit_chlorides} mg/l", False, True)

        u_water_suspended = get_val('water_suspended_matter_mg_l')
        limit_suspended = water_solids_limits["suspended_matter"]
        if u_water_suspended is not None:
            add_traceability('water_suspended_matter_mg_l', u_water_suspended)
            evaluate("Water - Suspended Matter", f"{u_water_suspended} mg/l", f"Max {limit_suspended} mg/l", float(u_water_suspended) <= limit_suspended)
        else:
            evaluate("Water - Suspended Matter", "Not Provided", f"Max {limit_suspended} mg/l", False, True)

        u_cl = get_val('measured_chloride_content')
        if u_cl is not None:
            add_traceability('measured_chloride_content', u_cl)
            limit_cl = is456_rules["CHLORIDE_LIMITS"]["max_chloride_kg_m3"].get(c_type, 0.6)
            evaluate("Chloride Content", f"{u_cl} kg/m³", f"Max {limit_cl} kg/m³", float(u_cl) <= limit_cl)
        else:
            evaluate("Chloride Content", "Not Provided", f"Depends on Concrete Type", False, True)
            
        u_so3 = get_val('measured_so3_percent')
        if u_so3 is not None:
            add_traceability('measured_so3_percent', u_so3)
            evaluate("Sulphate (SO3) Content", f"{u_so3}%", "Max 4.0%", float(u_so3) <= 4.0)
        else:
            evaluate("Sulphate (SO3) Content", "Not Provided", "Max 4.0%", False, True)

        # =====================================================
        # SECTION 4 — QUALITY CONTROL & SAMPLING (Dynamic Loop)
        # =====================================================
        u_vol = get_val('total_volume_m3')
        if u_vol is not None:
            evaluate("Total Volume", f"{u_vol} m³", "Required for sampling", True)
        else:
            evaluate("Total Volume", "Not Provided", "Required for sampling", False, True)
            
        u_cube = get_val('sampling_cube_size_mm')
        if u_cube is not None:
            add_traceability('sampling_cube_size_mm', u_cube)
            evaluate("Cube Size", f"{u_cube}mm", "150mm", float(u_cube) == 150)
        else:
            evaluate("Cube Size", "Not Provided", "150mm", False, True)

        u_samples = get_val('specified_sampling_sets')
        
        if u_vol is not None and u_samples is not None:
            add_traceability('total_volume_m3', u_vol)
            add_traceability('specified_sampling_sets', u_samples)
            
            s_rules = is456_rules["SAMPLING_FREQUENCY"]
            req_samples = 1 # fallback
            
            matched_threshold = False
            for threshold in s_rules["thresholds"]:
                if float(u_vol) <= threshold["max_m3"]:
                    req_samples = threshold["samples"]
                    matched_threshold = True
                    break
                    
            if not matched_threshold:
                base_samples = s_rules["base_50_samples"]
                extra_vol = float(u_vol) - 50
                extra_samples = (extra_vol // s_rules["additional_step_m3"]) + 1
                req_samples = base_samples + extra_samples
                
            evaluate("Sampling Sets", u_samples, f"Req {req_samples}", float(u_samples) >= req_samples)
        else:
            evaluate("Sampling Sets", "Not Provided", "Volume and Sets Required", False, True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        ledger.append({"Metric": "System Error", "Extracted Value": "Error", "Requirement": "N/A", "Status": f"Warning: {str(e)}"})

    return {"counts": counts, "ledger": ledger, "traceability": traceability}
