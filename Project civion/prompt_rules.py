"""Prompt rules shared by parser.py (the app) and
experiments/pipeline/extract_v2.py, so both extraction prompts stay identical.
"""

REFERENCES_RULE = """REFERENCES: A spec may state a requirement not as a value but by
    pointing elsewhere: to another IS code (e.g. "Grading of coarse aggregate
    shall conform to the requirements of IS 383.") or to a non-code source
    (e.g. "Nominal cover shall be as specified in the Drawings."). This is NOT
    missing data - do NOT treat it as a failure. Add one entry to
    "cross_references" per such statement: "parameter" = the exact field name
    from the JSON structure when the reference is about one of those fields
    (e.g. "member_covers"), otherwise a short snake_case name (e.g.
    "coarse_aggregate_grading"); "points_to" = the code exactly as written
    (e.g. "IS 383") or "drawings" or the other source named; "source_quote" =
    the exact sentence. If the same text also states a value, extract the
    value as usual too. If there are no such references, return an empty list."""


# A table value is only traceable if the quote shows both which column (header) and which row.
TABLE_QUOTE_RULE = """TABLE QUOTES: when a value is read from a table, its source quote
    is exactly TWO lines separated by a line break ("\\n" inside the JSON
    string). Line 1: the table's
    header row copied verbatim; if the header row is very long you may copy
    only the header text of the column you used (e.g. "REINFORCED CONCRETE -
    MINIMUM CEMENT CONTENT"), still verbatim. Line 2: the whole data row the
    value is in, copied verbatim with its row label and its "|" separators.
    Never merge header text and cell text into one line and never reword a cell."""


# Remarks are shown to the user next to the ledger row; they never change a result.
REMARKS_RULE = """REMARKS: when the document is ambiguous about a field - it states two
    different values, a value that applies only in some cases, or a value that
    conflicts with another clause - add "remarks": {"<field>": "one short factual
    sentence"}. Add no remark when the value is clear."""


def table_keys_hint():
    """Allowed group/item names for the IS 383 table fields, taken from database.py
    so the extraction uses exactly the names the auditor looks up."""
    from database import IS383_2016

    def names(table):
        limits = IS383_2016[table]["limits"]
        groups = list(limits)
        items = list(dict.fromkeys(i for g in limits.values() for i in g))
        return groups, items
    out = []
    for field, table in [("aggregate_deleterious_limits", "TABLE_2_DELETERIOUS"),
                         ("coarse_aggregate_grading", "TABLE_7_COARSE_GRADING"),
                         ("fine_aggregate_grading", "TABLE_9_FINE_GRADING"),
                         ("all_in_aggregate_grading", "TABLE_10_ALL_IN_GRADING")]:
        groups, items = names(table)
        out.append(f'"{field}" groups: {", ".join(groups)}; items: {", ".join(items)}')
    return "\n    ".join(out)
