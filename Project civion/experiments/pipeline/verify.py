"""Deterministic checks on pipeline outputs (no LLM).

- coverage(): every non-empty line of clean.md lands in exactly one section
  (as body text or as a heading line).
- check_quotes(): every source quote of an extraction is searched in
  clean.md (whitespace/case-normalized; "..." splits a quote into fragments
  that must each be found).
- Table quotes (a quote with a "|" or more than one line) must be two lines:
  line 1 a verbatim part of a table's header row, line 2 a verbatim part of
  a data row of the SAME table. Each line is checked on its own against the
  real table lines (pipe spacing, empty cells and list markers ignored).

Usage: python verify.py <extraction.json> [clean.md] [sections.json]
"""
import json
import re
import sys
from pathlib import Path

from common import OUT_DIR, read_json


def norm(s):
    s = str(s).lower().replace("’", "'")
    s = re.sub(r"[|*_`]", " ", s)
    return " ".join(s.split())


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


_ALNUM_CACHE = {}


def clean_alnum(clean_norm):
    if clean_norm not in _ALNUM_CACHE:
        _ALNUM_CACHE.clear()
        _ALNUM_CACHE[clean_norm] = alnum(clean_norm)
    return _ALNUM_CACHE[clean_norm]


def quote_found(quote, clean_norm):
    """Return (found: bool, missing_fragments: list)."""
    frags = [f.strip(" .;,:") for f in re.split(r"\.\.\.|…", str(quote))]
    frags = [f for f in frags if len(f) >= 2]
    if not frags:
        return False, [quote]
    missing = []
    for f in frags:
        nf = norm(f)
        if nf in clean_norm:
            continue
        # Docling sometimes breaks a sentence with a stray list marker
        # (a "- " between two halves of a sentence); compare alphanumerics
        # only as a fallback.
        if len(alnum(f)) >= 8 and alnum(f) in clean_alnum(clean_norm):
            continue
        missing.append(f)
    return not missing, missing


SEPARATOR = re.compile(r"^\|[\s:|-]+\|?$")


def norm_row(s):
    """Normalize one table line or quote line: no list marker, cells joined by
    ' | ', empty cells dropped, whitespace and case folded."""
    s = re.sub(r"^\s*[-*]\s+", "", str(s).replace("’", "'"))
    cells = [" ".join(c.split()).lower() for c in s.split("|")]
    return " | ".join(c for c in cells if c)


def parse_tables(clean_md):
    """[{line, header, rows}] for every markdown table; header and rows normalized."""
    tables, cur = [], None
    for i, line in enumerate(clean_md.splitlines(), 1):
        if line.strip().startswith("|"):
            if cur is None:
                cur = {"line": i, "header": norm_row(line), "rows": []}
                tables.append(cur)
            elif not SEPARATOR.match(line.strip()):
                cur["rows"].append(norm_row(line))
        else:
            cur = None
    return tables


def is_table_quote(quote):
    lines = [l for l in str(quote).splitlines() if l.strip()]
    return len(lines) > 1 or "|" in str(quote)


def number_in(n, text):
    """True if number n (e.g. '0.55', '290', '200.0') appears as a number in text."""
    want = float(n)
    return any(float(x) == want for x in re.findall(r"\d+(?:\.\d+)?", text))


def table_quote_found(quote, tables, value=None):
    """Return (found, problems, info). found only if line 1 is part of a
    table's header row and line 2 part of a data row of the same table."""
    # Line 1 = header row; every further line = a data row of the same table
    # (a whole-table value such as a grading table may quote several rows).
    # Markdown separator lines ("|---|") in the quote are ignored.
    lines = [l for l in str(quote).splitlines() if l.strip() and not SEPARATOR.match(l.strip())]
    if len(lines) < 2:
        return False, [f"table quote must be a header row + data row(s), got {len(lines)} line(s)"], {}
    head, rows = norm_row(lines[0]), [norm_row(l) for l in lines[1:]]
    row = rows[0]
    head_in = [t for t in tables if head and head in t["header"]]
    both = [t for t in head_in if all(r and any(r in tr for tr in t["rows"]) for r in rows)]
    problems = []
    if not head_in:
        problems.append(f"line 1 is not part of any table header row: {lines[0][:80]}")
    elif not both:
        problems.append(f"a quoted row is not a data row of that table: {lines[1][:80]}")
    info = {"table_line": both[0]["line"]} if both else {}
    # Extra signal (does not affect found): is the extracted number in the quoted row?
    if both and isinstance(value, (int, float)) and not isinstance(value, bool):
        info["value_in_row"] = number_in(value, row)
    return not problems, problems, info


def check_quotes(extraction, clean_md):
    clean_norm = norm(clean_md)
    tables = parse_tables(clean_md)
    rows = []
    quotes = extraction.get("source_quotes") or {}
    for field, q in quotes.items():
        if q is None:
            continue
        if str(q).startswith(("Exposure condition determined outside", "Concrete type determined outside")):
            rows.append({"field": field, "quote": q, "found": None, "note": "stamped from CLI arg"})
            continue
        if is_table_quote(q):
            ok, missing, info = table_quote_found(q, tables, extraction.get(field))
            rows.append({"field": field, "value": extraction.get(field), "quote": q, "kind": "table",
                         "found": ok, "missing_fragments": missing, **info})
            continue
        ok, missing = quote_found(q, clean_norm)
        rows.append({"field": field, "value": extraction.get(field), "quote": q, "kind": "text", "found": ok,
                     "missing_fragments": missing})
    for x in extraction.get("cross_references") or []:
        q = x.get("source_quote")
        ok, missing = quote_found(q, clean_norm) if q else (False, ["<no quote>"])
        rows.append({"field": f"cross_ref:{x.get('parameter')}->{(x.get('points_to') or x.get('referenced_code'))}",
                     "quote": q, "found": ok, "missing_fragments": missing})
    return rows


def coverage(clean_md, sections):
    lines = [l.strip() for l in clean_md.splitlines() if l.strip()]
    covered = []
    for s in sections:
        for h in s["heading"].split(" / "):
            covered.append(h.strip())
        covered += [l.strip() for l in s["text"].splitlines() if l.strip()]
    heading_lines = {re.sub(r"^#+\s*", "", l) for l in lines}
    missing = [l for l in lines if l not in covered and re.sub(r"^#+\s*", "", l) not in covered]
    dup = len(covered) - len(set(covered))
    return {"clean_lines": len(lines), "covered_lines": len(covered), "uncovered": missing[:20],
            "n_uncovered": len(missing), "duplicate_line_texts": dup, "_heading_lines": len(heading_lines)}


if __name__ == "__main__":
    ext = read_json(sys.argv[1])
    clean_md = Path(sys.argv[2] if len(sys.argv) > 2 else OUT_DIR / "clean.md").read_text(encoding="utf-8")
    secs = read_json(sys.argv[3] if len(sys.argv) > 3 else OUT_DIR / "sections.json")
    print(json.dumps(coverage(clean_md, secs), indent=1))
    for r in check_quotes(ext, clean_md):
        print(("OK  " if r["found"] else "N/A " if r["found"] is None else "MISS"), r["field"], "|",
              str(r["quote"])[:110], "|", r.get("missing_fragments") or "")
