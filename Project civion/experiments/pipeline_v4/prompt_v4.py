"""v4 prompt: the whole document in one call, only the fields of database.PARAMETERS.

Per-field rules are taken from experiments/pipeline/groups.py (the tested v2
wording) so v2 and v4 ask for the same thing; only the grading-table fields
(no excerpt ids in v4) and the three site SO3 fields (v2 did not extract them)
get their own wording here. Shared rules come from prompt_rules.py.
"""
import gemini_call  # noqa: F401  (puts the project root and experiments/pipeline on sys.path)
from database import PARAMETERS
from groups import PARAM_GROUP, GROUPS
from prompt_rules import REFERENCES_RULE, REMARKS_RULE, TABLE_QUOTE_RULE, table_keys_hint

# Extracted from the document = every PARAMETERS entry not supplied by the user or derived.
FIELDS = [f for f, s in PARAMETERS.items() if s.get("from") not in ("user", "derived")]
TABLE_FIELDS = [f for f in FIELDS if PARAMETERS[f]["shape"] in ("set_max", "set_range")]
GRADING_FIELDS = [f for f in FIELDS if PARAMETERS[f]["shape"] == "set_range"]
TYPES = ("value", "range", "table", "reference", "conditional", "needs_review", "not_found")

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


def field_line(f, table_mode):
    if f in SITE_RULES:
        typ, rule = SITE_RULES[f]
    elif f in GRADING_FIELDS and table_mode == "python":
        typ = '{"columns": {"<column header copied verbatim>": "<designation>"}}'
        rule = (f"the document's own {PARAMETERS[f]['metric'].lower()} table (percentage passing per IS sieve): "
                f"for each column, which {GRADING_DESIGNATIONS[f]} it is. Copy each column header exactly as "
                f"written. Do not copy the cells")
    elif f in GRADING_FIELDS:
        typ = '{"<designation>": {"<sieve>": [low, high]}}'
        rule = (f"the document's own {PARAMETERS[f]['metric'].lower()} table, cell by cell: one group per "
                f"{GRADING_DESIGNATIONS[f]} column, one item per IS sieve row; a single value v is [v, v]; "
                f'skip cells marked "--"')
    else:
        p = next(p for p in GROUPS[PARAM_GROUP[f]].params if p.name == f)
        typ, rule = p.type, p.rule
    return f'  "{f}": {typ},   // {rule}'


def group_notes():
    """The v2 group notes that still apply (water table, aggregate tables)."""
    notes = list(GROUPS["materials"].notes)
    notes.append('Each "water_*_mg_l" quote is TWO lines: that table\'s header row, then the row of the value. '
                 "A quote that is only the data row is rejected.")
    notes.append(
        "AGGREGATE TABLES: fill these only from a table that states the limits (deleterious limits: a single "
        'value v is v; skip cells marked "--"). If the document has its own table, ALWAYS fill the field from it, '
        'even when it also says the aggregate shall conform to IS 383 (then add that cross_references entry too). '
        "Leave the field null only when there is no table at all. Use exactly these group / item names "
        "(sieves written like '4.75 mm', '600 um'):\n    " + table_keys_hint())
    return "\n".join(f"NOTE: {n}" for n in notes)


def build_system(exposure, concrete_type, table_mode="python"):
    fields = "\n".join(field_line(f, table_mode) for f in FIELDS)
    grading_note = ("For the three grading fields give ONLY the column -> designation map; Python reads the "
                    "cells from the document and builds their quote, so leave their source_quotes entry out."
                    if table_mode == "python" else "")
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
{grading_note}

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
