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
