"""Deterministic checks on pipeline outputs (no LLM).

- coverage(): every non-empty line of clean.md lands in exactly one section
  (as body text or as a heading line).
- check_quotes(): every source quote of an extraction is searched in
  clean.md (whitespace/case-normalized; "..." splits a quote into fragments
  that must each be found). Table-row quotes ("a | b") are matched cell by cell.

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
        # Table-row quote: accept when every cell is present (Docling pads cells).
        cells = [norm(c) for c in str(f).split("|") if norm(c)]
        if len(cells) > 1 and all(c in clean_norm for c in cells):
            continue
        missing.append(f)
    return not missing, missing


def check_quotes(extraction, clean_md):
    clean_norm = norm(clean_md)
    rows = []
    quotes = extraction.get("source_quotes") or {}
    for field, q in quotes.items():
        if q is None:
            continue
        if str(q).startswith(("Exposure condition determined outside", "Concrete type determined outside")):
            rows.append({"field": field, "quote": q, "found": None, "note": "stamped from CLI arg"})
            continue
        ok, missing = quote_found(q, clean_norm)
        rows.append({"field": field, "value": extraction.get(field), "quote": q, "found": ok,
                     "missing_fragments": missing})
    for x in extraction.get("cross_references") or []:
        q = x.get("source_quote")
        ok, missing = quote_found(q, clean_norm) if q else (False, ["<no quote>"])
        rows.append({"field": f"cross_ref:{x.get('parameter')}->{x.get('referenced_code')}",
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
