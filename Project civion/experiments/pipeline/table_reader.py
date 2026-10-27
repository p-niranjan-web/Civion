"""Read a grading-type table cell by cell in Python.

LLMs misalign columns in wide tables (BLR's 11-column coarse grading table:
values shifted to the wrong nominal size). For such fields the model only
says WHICH table (excerpt id) and WHICH column is which IS designation:

    {"table": "S028.U1",
     "columns": {"<column header text, verbatim>": "graded 20 mm", ...}}

and this module reads the cells: rows are IS sieves ("4.75 mm", "600 micron"),
cells are numbers or ranges ("85 to 100", "0-10"); "--" means no limit.
The quote is built from the document's own lines, so it is verbatim.
"""
import re

SEPARATOR = re.compile(r"^\|[\s:|-]+\|?$")
SIEVE = re.compile(r"^(\d+(?:\.\d+)?)\s*(mm|microns?|µm|μm|um)$", re.I)


def norm(s):
    return " ".join(str(s).lower().replace("µ", "u").replace("μ", "u").split())


def sieve_name(label):
    m = SIEVE.match(str(label).strip())
    if not m:
        return None
    unit = "mm" if m.group(2).lower() == "mm" else "um"
    return f"{m.group(1)} {unit}"


def cell_range(text):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(text))]
    if not nums or str(text).strip() in ("--", "-", "—"):
        return None
    lo, hi = min(nums), max(nums)
    return [int(lo) if lo.is_integer() else lo, int(hi) if hi.is_integer() else hi]


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def read_table(answer, units_by_id):
    """answer = {"table": unit id, "columns": {header: designation}} ->
    (cells {designation: {sieve: [lo, hi]}}, verbatim quote) or (None, problem)."""
    if not isinstance(answer, dict) or not isinstance(answer.get("columns"), dict):
        return None, "answer is not {table, columns}"
    unit = units_by_id.get(str(answer.get("table", "")).strip().strip("[]"))
    if unit is None:
        return None, f"unknown table id {answer.get('table')!r}"
    lines = [l for l in unit["text"].splitlines() if l.strip().startswith("|")]
    if not lines:
        return None, "excerpt has no table"
    header = split_row(lines[0])
    col_of = {}
    for head_text, designation in answer["columns"].items():
        idx = [i for i, h in enumerate(header) if norm(head_text) and (norm(head_text) == norm(h))]
        idx = idx or [i for i, h in enumerate(header) if norm(head_text) and norm(head_text) in norm(h)]
        if len(idx) == 1:
            col_of[designation] = idx[0]
    if not col_of:
        return None, "no column header matched"
    cells, used = {}, []
    for line in lines[1:]:
        if SEPARATOR.match(line.strip()):
            continue
        row = split_row(line)
        sieve = sieve_name(row[0]) if row else None
        if not sieve:
            continue
        for designation, i in col_of.items():
            r = cell_range(row[i]) if i < len(row) else None
            if r is not None:
                cells.setdefault(designation, {})[sieve] = r
        used.append(line.strip())
    if not cells:
        return None, "no sieve rows found"
    return cells, "\n".join([lines[0].strip()] + used)
