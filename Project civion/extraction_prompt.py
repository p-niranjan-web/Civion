"""Extraction prompt: the whole document in ONE Gemini call, only the fields of database.PARAMETERS.

This is the v4 prompt (experiments/pipeline_v4/prompt_v4.py) in its "model copies the cells"
form: Gemini reads the three aggregate grading tables itself, cell by cell, and writes their
source quotes. No Python table reader is involved.

Per-field wording comes from experiments/pipeline/groups.py (the tested v2 wording), so a
field is described the same way in every pipeline version. To add a parameter: add it to
database.PARAMETERS and one entry to FIELD_RULES below (the import-time check enforces both).
"""
from database import PARAMETERS
from prompt_rules import REFERENCES_RULE, REMARKS_RULE, TABLE_QUOTE_RULE, table_keys_hint

# Extracted from the document = every PARAMETERS entry not supplied by the user or derived.
FIELDS = [f for f, s in PARAMETERS.items() if s.get("from") not in ("user", "derived")]
GRADING_FIELDS = [f for f in FIELDS if PARAMETERS[f]["shape"] == "set_range"]
TYPES = ("value", "range", "table", "reference", "conditional", "needs_review", "not_found")

# name -> (JSON type shown to the model, how to read it from a spec)
FIELD_RULES = {
    "specified_grade": ("string like M25",
        "the grade specified for the structural (reinforced) concrete. If the text only lists all "
        "possible grades in a reference table, return null."),
    "specified_characteristic_strength": ("int (N/mm2)",
        "characteristic compressive strength of the specified grade at 28 days"),
    "specified_sigma": ("int (N/mm2)",
        "assumed/specified standard deviation used for mix design"),
    "specified_min_cement": ("int (kg/m3)",
        "minimum cement content. If only a range is stated, use its lower bound."),
    "specified_max_cement": ("int (kg/m3)",
        "maximum cement content (not the minimum)"),
    "specified_wc": ("float, or [low, high]",
        "maximum water-cement (free water/cement) ratio. If a range such as 'between 0.45 to 0.50' "
        "is stated, return [0.45, 0.50]. A ratio stated in a mix-design clause takes priority over a "
        "general table value; if both exist, add a remark naming both values."),
    "freezing_thawing_exposure": ("bool",
        "true only if the text states the structure is exposed to freezing and thawing; null if not "
        "stated (an exposure-class description that merely mentions freezing is NOT a statement)"),
    "measured_chloride_content": ("float (kg/m3 of concrete)",
        "chloride (chloride ion) content limit of the concrete, in kg per m3 of concrete"),
    "measured_so3_percent": ("float (% SO3)",
        "sulphate (SO3) content limit of the concrete mix, as percent by mass of cement"),
    "cement_type": ("OPC|PPC|PSC|SRC|Mineral Admixture",
        "the cement type required for the work (the default/general requirement, not a list of "
        "alternatives that need approval)"),
    "water_ph": ("float, or [low, high]",
        "pH of mixing/curing water: 'not less than 6' -> 6; 'between 6 and 9' -> [6, 9]"),
    "water_organic_mg_l": ("float (mg/l)", "max organic solids in water"),
    "water_inorganic_mg_l": ("float (mg/l)", "max inorganic solids in water"),
    "water_sulphates_mg_l": ("string (mg/l with basis)",
        "max sulphates in water, with the basis the document states, e.g. '500 as SO4' or '400 as SO3'"),
    "water_chlorides_mg_l": ("float (mg/l)", "max chlorides in water for the given concrete type"),
    "water_suspended_matter_mg_l": ("float (mg/l)", "max suspended matter in water"),
    "mixing_time_minutes": ("int", "minimum mixing time in the mixer, in minutes"),
    "transport_time_minutes": ("int",
        "maximum time from mixing/production to placing (transport/delivery), in minutes; convert "
        "hours to minutes. Use the general limit, not a special hot-weather reduction."),
    "compaction_method": ("mechanical vibrator|manual|hand|ramming", "how concrete must be compacted"),
    "specified_slump_mm": ("int (mm), or [low, high]",
        "specified slump in mm; a range such as '25 mm to 35 mm' -> [25, 35]"),
    "curing_days": ("int",
        "minimum moist-curing period for normal (not mass) concrete, in days. If the text gives "
        "consecutive periods (e.g. 7 days of one method then a further 7 days of another), use the "
        "total."),
    "member_covers": ('{"Beams": int, "Columns": int, "Slabs": int}',
        "nominal cover in mm per member type; null for a member whose cover is not stated as a number"),
    "fire_resistance_rating": ("0.5hr|1hr|1.5hr|2hr|4hr", "required fire resistance rating of the members"),
    "sampling_cube_size_mm": ("int (mm)", "size of the test cubes in mm (convert cm to mm)"),
    "specified_sampling_sets": ("int",
        "number of samples/sets required, only if stated as a single number for this work"),
    "total_volume_m3": ("int (m3)",
        "total quantity of concrete for the work, only if stated as a single project quantity"),
    "sampling_frequency":
        ('[{"from_m3": float, "to_m3": float or null, "samples": int, "extra_per_m3": float or null}]',
         "minimum sampling frequency rule: one entry per quantity band (e.g. '5 to 15 cu.m -> 2 samples'); "
         "the open-ended last band ('more than 50: 4 + one per additional 50 cu.m') has to_m3 null and "
         "extra_per_m3 50. Its quote goes in source_quotes (table header row + one band row). If the rule "
         "appears more than once, use the most complete copy and add a remark."),
    "aggregate_deleterious_limits": ('{"<aggregate kind>": {"<substance>": float}}',
        "maximum percentages of deleterious materials, per aggregate kind and substance"),
}

# Site values: not in a normal spec, so they get their own wording.
SITE_RULES = {
    "soil_total_so3_percent": ("float (% SO3)",
        "total SO3 content of the soil AT THIS SITE, as measured / stated for this project. NOT the class "
        "boundaries of a sulphate-attack classification table (e.g. IS 456 Table 4): if the document only "
        "reproduces such a table, return null"),
    "soil_extract_2_1_so3_gl": ("float (g/l SO3)",
        "SO3 in a 2:1 water:soil extract of the soil AT THIS SITE, as measured / stated for this project; "
        "null if the document only reproduces a classification table"),
    "groundwater_so3_gl": ("float (g/l SO3)",
        "SO3 in the groundwater AT THIS SITE, as measured / stated for this project; null if the document "
        "only reproduces a classification table"),
}

GRADING_DESIGNATIONS = {
    "coarse_aggregate_grading": "nominal-size designation (single-sized / graded)",
    "fine_aggregate_grading": "grading zone",
    "all_in_aggregate_grading": "nominal size",
}

WATER_TABLE_NOTE = (
    'The "water_*_mg_l" fields come from a "PERMISSIBLE LIMITS FOR SOLIDS (IN WATER)" style table '
    "(mixing/curing water quality per IS 456 Table 1) - do NOT confuse them with soil/groundwater "
    "sulphate-attack tables.")


def _check_fields_covered():
    covered = set(FIELD_RULES) | set(SITE_RULES) | set(GRADING_DESIGNATIONS)
    if set(FIELDS) != covered:
        raise RuntimeError(
            "extraction_prompt.py and database.PARAMETERS disagree: only in database "
            f"{sorted(set(FIELDS) - covered)}, only in prompt {sorted(covered - set(FIELDS))}")


_check_fields_covered()


def field_line(f):
    if f in SITE_RULES:
        typ, rule = SITE_RULES[f]
    elif f in GRADING_FIELDS:
        typ = '{"<designation>": {"<sieve>": [low, high]}}'
        rule = (f"the document's own {PARAMETERS[f]['metric'].lower()} table, cell by cell: one group per "
                f"{GRADING_DESIGNATIONS[f]} column, one item per IS sieve row; a single value v is [v, v]; "
                f'skip cells marked "--"')
    else:
        typ, rule = FIELD_RULES[f]
    return f'  "{f}": {typ},   // {rule}'


def group_notes():
    notes = [WATER_TABLE_NOTE,
             'Each "water_*_mg_l" quote is TWO lines: that table\'s header row, then the row of the value. '
             "A quote that is only the data row is rejected.",
             "AGGREGATE TABLES: fill these only from a table that states the limits (deleterious limits: a single "
             'value v is v; skip cells marked "--"). If the document has its own table, ALWAYS fill the field from it, '
             'even when it also says the aggregate shall conform to IS 383 (then add that cross_references entry too). '
             "Leave the field null only when there is no table at all. Use exactly these group / item names "
             "(sieves written like '4.75 mm', '600 um'):\n    " + table_keys_hint()]
    return "\n".join(f"NOTE: {n}" for n in notes)


def build_system(exposure, concrete_type):
    fields = "\n".join(field_line(f) for f in FIELDS)
    return f"""You are a civil engineering parser. You read a concrete specification and return
STRICTLY valid JSON. Do NOT invent values. If a value is not in the document, return null.

TASK: the user message is a WHOLE concrete specification (Markdown converted from a PDF;
tables are Markdown tables, headings start with #). Extract ONLY the fields listed below.
Ignore every other requirement in the document.

CONTEXT (given by the user, not in the document): exposure condition = "{exposure}";
concrete type = "{concrete_type}". The cement type must be read from the document.

RULES
- Use only values stated in the document, or read from a table of the document. NEVER fill a
  value from your own knowledge of IS codes or good practice: if the document only says
  "as per IS 456" (or similar) for a field, the value is null and the statement goes in
  cross_references.
- A table that merely lists all possible options (e.g. every concrete grade with its
  strength, or every exposure class) does not specify which one applies: do not pick a row
  from it unless the document says which row is required.
- TABLE RESOLUTION: when a value is only given in a requirements table keyed by exposure
  class (rows) and concrete type / parameter (columns), read the "{exposure}" row and the
  "{concrete_type}" column and return that cell.
- CONDITIONAL VALUES: when the document gives different values for different cases, return
  the value that applies to the exposure and concrete type above. A value that applies only
  under a condition nobody has supplied (hot weather, cold weather, mass concrete, a
  particular member or method) is NOT the general value: return the general value and put
  the conditional one in a remark.
- NEEDS REVIEW: when you cannot decide the value with confidence, return null or your best
  value, and say why in a remark.
- SINGLE VALUE -> a plain number or string. RANGE -> [low, high].
- CHEMICAL BASIS: keep the basis the document states inside the value, e.g. "500 as SO4".
- SOURCE QUOTES: for every non-null field, copy the supporting text VERBATIM from the
  document - a whole sentence, or (for a table) as below - not just the number. Do not
  shorten a quote with "...".
{TABLE_QUOTE_RULE}
  Example of a table quote (2 lines; the first line is the table's header row, even when
  the header row has an empty first cell):
  "| Item | Limit, max |\\n| Item A | 200 mg/l |"
- REFERENCES apply to every field above, including member_covers (cover "as specified in
  the drawings" is a reference with points_to "drawings").
{REFERENCES_RULE}
{REMARKS_RULE}
- FIELD INFO: for every field, "field_info" gives "type" (one of {", ".join(TYPES)}) and
  "location" = the heading path of the place the value was read from, headings copied as
  written and joined by " > " (e.g. "3.6 CONCRETE > P. Curing"); "" when not found. No page numbers.
{group_notes()}


FIELDS (name: type  // what to extract)
{fields}

Return exactly ONE JSON object:
{{
  "<each field above>": <value or null>,
  "cross_references": [ {{ "parameter": "field name from above, or a short snake_case name", "points_to": "IS code like 'IS 383', or 'drawings' / other source", "source_quote": "exact quote" }} ],
  "source_quotes": {{ "<field>": "verbatim quote for every non-null field" }},
  "remarks": {{ "<field>": "one short sentence, only when ambiguous / conditional / needs review" }},
  "field_info": {{ "<field>": {{ "type": "...", "location": "..." }} }}
}}"""


def build_user(doc_text):
    return f"SPECIFICATION DOCUMENT:\n\n{doc_text}\n\nEND OF DOCUMENT. Return the JSON object now."
