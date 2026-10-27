"""Fixed, document-independent extraction groups (v2).

Each parameter of parser.py's schema lives in exactly ONE group. Formwork
fields and the fields supplied from outside the document (exposure,
concrete_type, site soil/groundwater SO3) are excluded on purpose.

To add a parameter: add one P(...) line to one group. Fields:
  name   - key in the extraction JSON (auditor.py reads it)
  type   - JSON type shown to the model
  rule   - how to read it from a spec (document-independent wording)
  cues   - a few plain words that hint a text unit may feed this parameter;
           used only as routing hints (see route.py), never to extract values
"""
from collections import namedtuple

P = namedtuple("P", "name type rule cues")
Group = namedtuple("Group", "title routing_desc params notes")

GROUPS = {
    "grade_strength": Group(
        "Concrete grade and strength",
        "concrete grade designations (M20, M25...), characteristic compressive strength, "
        "target mean strength, standard deviation, grade tables",
        [
            P("specified_grade", "string like M25",
              "the grade specified for the structural (reinforced) concrete. If the text only lists all "
              "possible grades in a reference table, return null.",
              ("grade", "M 2", "M2", "M3", "M4")),
            P("specified_characteristic_strength", "int (N/mm2)",
              "characteristic compressive strength of the specified grade at 28 days",
              ("characteristic", "compressive strength", "N/mm")),
            P("specified_sigma", "int (N/mm2)",
              "assumed/specified standard deviation used for mix design",
              ("standard deviation", "target mean")),
        ],
        [],
    ),
    "durability": Group(
        "Durability limits",
        "minimum/maximum cement content, water-cement ratio, exposure-condition tables, sulphate-attack "
        "tables, freezing and thawing, chloride or sulphate content limits of the concrete mix",
        [
            P("specified_min_cement", "int (kg/m3)",
              "minimum cement content. If only a range is stated, use its lower bound.",
              ("cement content", "kg/m")),
            P("specified_max_cement", "int (kg/m3)",
              "maximum cement content (not the minimum)",
              ("maximum cement", "cement content", "kg/m")),
            P("specified_wc", "float",
              "maximum water-cement (free water/cement) ratio. If a range such as 'between 0.45 to 0.50' "
              "is stated, use the upper bound. A ratio stated in a mix-design clause takes priority over a "
              "general table value; give both quotes if both exist.",
              ("water cement", "water-cement", "w/c", "ratio")),
            P("freezing_thawing_exposure", "bool",
              "true only if the text states the structure is exposed to freezing and thawing; null if not "
              "stated (an exposure-class description that merely mentions freezing is NOT a statement)",
              ("freezing", "thawing", "air entrain")),
            P("measured_chloride_content", "float (kg/m3 of concrete)",
              "chloride (chloride ion) content limit of the concrete, in kg per m3 of concrete",
              ("chloride",)),
            P("measured_so3_percent", "float (% SO3)",
              "sulphate (SO3) content limit of the concrete mix, as percent by mass of cement",
              ("so3", "sulphate", "sulfate")),
        ],
        [],
    ),
    "materials": Group(
        "Materials: cement, water, admixtures, aggregates",
        "cement types, mixing/curing water quality (pH, solids limits table), admixtures, aggregates",
        [
            P("cement_type", "OPC|PPC|PSC|SRC|Mineral Admixture",
              "the cement type required for the work (the default/general requirement, not a list of "
              "alternatives that need approval)",
              ("cement", "portland")),
            P("water_ph", "float",
              "minimum pH of mixing/curing water (if a range like 'not less than 6' is given, the lower bound)",
              ("ph",)),
            P("water_organic_mg_l", "float (mg/l)", "max organic solids in water", ("organic",)),
            P("water_inorganic_mg_l", "float (mg/l)", "max inorganic solids in water", ("inorganic",)),
            P("water_sulphates_mg_l", "float (mg/l)", "max sulphates (as SO4) in water", ("sulphates", "so4")),
            P("water_chlorides_mg_l", "float (mg/l)",
              "max chlorides in water for the given concrete type", ("chlorides",)),
            P("water_suspended_matter_mg_l", "float (mg/l)", "max suspended matter in water", ("suspended",)),
        ],
        ['The "water_*_mg_l" fields come from a "PERMISSIBLE LIMITS FOR SOLIDS (IN WATER)" style table '
         "(mixing/curing water quality per IS 456 Table 1) - do NOT confuse them with soil/groundwater "
         "sulphate-attack tables."],
    ),
    "production": Group(
        "Concrete production, placing and curing",
        "mix design, trial mixes, batching, mixing time, transport/delivery time, placing, compaction, "
        "slump/workability, construction joints, hot/cold weather concreting, curing period, mass concrete",
        [
            P("mixing_time_minutes", "int",
              "minimum mixing time in the mixer, in minutes", ("mixer", "mixing", "minutes")),
            P("transport_time_minutes", "int",
              "maximum time from mixing/production to placing (transport/delivery), in minutes; convert "
              "hours to minutes. Use the general limit, not a special hot-weather reduction.",
              ("minutes", "transport", "delivery", "placed within", "hrs")),
            P("compaction_method", "mechanical vibrator|manual|hand|ramming",
              "how concrete must be compacted", ("vibrat", "compact")),
            P("specified_slump_mm", "int (mm)",
              "specified slump in mm. If a range is given, use its upper bound.", ("slump", "workability")),
            P("curing_days", "int",
              "minimum moist-curing period for normal (not mass) concrete, in days. If the text gives "
              "consecutive periods (e.g. 7 days of one method then a further 7 days of another), use the "
              "total.",
              ("curing", "cured", "days")),
        ],
        [],
    ),
    "cover_sampling": Group(
        "Nominal cover and sampling/testing",
        "nominal cover to reinforcement per member, fire resistance rating, cube size, sampling/testing "
        "frequency tables, quantity of concrete, acceptance criteria",
        [
            P("member_covers", '{"Beams": int, "Columns": int, "Slabs": int}',
              "nominal cover in mm per member type; null for a member whose cover is not stated as a number",
              ("cover",)),
            P("fire_resistance_rating", "0.5hr|1hr|1.5hr|2hr|4hr",
              "required fire resistance rating of the members", ("fire",)),
            P("sampling_cube_size_mm", "int (mm)",
              "size of the test cubes in mm (convert cm to mm)", ("cube", "cm", "mm")),
            P("specified_sampling_sets", "int",
              "number of samples/sets required, only if stated as a single number for this work",
              ("sample", "samples", "frequency")),
            P("total_volume_m3", "int (m3)",
              "total quantity of concrete for the work, only if stated as a single project quantity",
              ("cu.m", "m3", "quantity", "volume")),
        ],
        [],
    ),
}

# Every group may also emit cross_references (a requirement deferred to another code).
PARAM_GROUP = {p.name: g for g, grp in GROUPS.items() for p in grp.params}
ALL_PARAMS = list(PARAM_GROUP)

assert len(ALL_PARAMS) == len(set(ALL_PARAMS)), "a parameter is in two groups"
