"""Read a grading table cell by cell in Python (v4 version of experiments/pipeline/table_reader.py).

v2's reader looked the table up by unit id; v4 sends the whole document and has
no units, so the table is FOUND in the document: the one whose header row
contains every column header the model named. The model only maps columns:

    {"columns": {"<column header text, verbatim>": "graded 20 mm", ...}}

Cells are then read by table_reader.read_table (unchanged), so the rows,
ranges and "--" handling are the same as in v2.
"""
import gemini_call  # noqa: F401  (puts experiments/pipeline on sys.path)
import table_reader
from table_reader import norm, split_row


def markdown_tables(doc):
    """[[line, ...], ...] - each run of consecutive "|" lines is one table."""
    tables, cur = [], None
    for line in doc.splitlines():
        if line.strip().startswith("|"):
            if cur is None:
                cur = []
                tables.append(cur)
            cur.append(line)
        else:
            cur = None
    return tables


def find_table(columns, doc):
    """Index of the one table whose header row contains every named column header."""
    heads = [norm(h) for h in columns if norm(h)]
    hits = []
    for i, t in enumerate(markdown_tables(doc)):
        header = [norm(h) for h in split_row(t[0])]
        if heads and all(any(h == c or h in c for c in header) for h in heads):
            hits.append(i)
    return hits


def read_table(answer, doc):
    """answer = {"columns": {header: designation}} -> (cells, verbatim quote) or (None, problem)."""
    if not isinstance(answer, dict) or not isinstance(answer.get("columns"), dict) or not answer["columns"]:
        return None, "answer is not {columns: {...}}"
    hits = find_table(answer["columns"], doc)
    if not hits:
        return None, "no table header contains all the named columns"
    if len(hits) > 1:
        return None, f"{len(hits)} tables match the named columns"
    lines = markdown_tables(doc)[hits[0]]
    return table_reader.read_table({"table": "T", "columns": answer["columns"]}, {"T": {"text": "\n".join(lines)}})
