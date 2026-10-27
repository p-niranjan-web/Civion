"""Per-parameter fallback keyword search over a Docling-parsed spec (Markdown).

When the LLM extraction returns MISSING for a parameter, this search runs over
the rest of the document for that one parameter and returns candidate units
(sentence / list item / table row) that contain a term AND a value hint
(or just a term, for descriptive parameters) and no exclude phrase.

Stdlib only. Usage:
    python search.py --doc ../parse_test/docling_output.md --keywords keywords.json
    python search.py --doc ... --keywords ... --param specified_wc
    python search.py --doc ... --keywords ... --out hits.json
"""
import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
_CHAR_MAP = {
    "\u00b3": "3", "\u00b2": "2", "\u2083": "3", "\u2084": "4", "\u2082": "2",
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2010": "-", "\u2011": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00a0": " ", "\u00d7": "x",
}


def normalize(text):
    """Lowercase, map unicode super/subscripts and dashes, treat a hyphen
    between letters as a space (water-cement == water cement), collapse
    whitespace."""
    text = "".join(_CHAR_MAP.get(c, c) for c in text).lower()
    text = re.sub(r"(?<=[a-z])\s*-\s*(?=[a-z])", " ", text)
    text = text.replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def term_regex(term):
    if term.startswith("re:"):          # raw regex over normalized text
        return re.compile(term[3:])
    t = normalize(term)
    body = r"\s*".join(re.escape(p) for p in t.split(" ")) if " " in t else re.escape(t)
    left = r"(?<![a-z0-9])" if re.match(r"[a-z0-9]", t) else ""
    right = r"(?![a-z0-9])" if re.search(r"[a-z0-9]$", t) else ""
    return re.compile(left + body + right)


# ---------------------------------------------------------------------------
# Unit splitting
# ---------------------------------------------------------------------------
_ABBREV = ("cl.", "no.", "nos.", "e.g.", "i.e.", "viz.", "fig.", "approx.", "min.",
           "max.", "max", "min", "etc.", "vol.", "ref.", "sec.", "para.", "dia.", "mm.", "st.")


def split_sentences(text):
    """Split a paragraph on . ; ? ! followed by space + capital/opening bracket,
    without splitting decimals or common abbreviations (Cl. 5.4, No. 2, e.g.)."""
    out, start = [], 0
    for m in re.finditer(r"[.;?!]\s+(?=[A-Z(\[\"'])", text):
        end = m.start() + 1
        last_word = text[start:end].split()[-1].lower() if text[start:end].split() else ""
        if last_word in _ABBREV or re.fullmatch(r"[a-z]\.", last_word) or re.fullmatch(r"\(?[0-9ivx]+[.)]", last_word):
            continue
        out.append(text[start:end].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return [s for s in out if s]


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


_UNIT_TOKEN = re.compile(r"\[?\b[a-z]+\s*/\s*[a-z]+\s*\d?\s*\]?", re.I)


def _is_header_row(cells):
    """A sub-header row: units only ('Kg/m 3'), column numbering ('(1) | (2)'
    or '1 | 2'), or no digits at all. Parsed specs often split a table's
    header over several rows, and the unit lives in the second one."""
    for pos, c in enumerate(cells, 1):
        c = _UNIT_TOKEN.sub("", c)
        c = re.sub(r"\(\d+\)", "", c).strip(" []")
        if not re.search(r"\d", c):
            continue
        if c == str(pos):          # column-numbering row
            continue
        return False
    return True


def _blocks(lines):
    """Group lines into blocks: heading, list_item, paragraph, table."""
    blocks, i = [], 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append((i + 1, lines[i]))
                i += 1
            blocks.append({"kind": "table", "line": rows[0][0], "rows": rows})
            continue
        if s.startswith("#"):
            blocks.append({"kind": "heading", "line": i + 1, "text": s.lstrip("#").strip()})
        elif re.match(r"^([-*+]|\d+[.)]|\([a-z0-9]+\)|[a-z][.)])\s+", s):
            blocks.append({"kind": "list_item", "line": i + 1, "text": s})
        else:
            blocks.append({"kind": "paragraph", "line": i + 1, "text": s})
        i += 1
    return blocks


def _merge_page_breaks(blocks):
    """A PDF page break splits one sentence into two blocks; the second half
    then starts with a lowercase word (Docling often prefixes it with '- ').
    Re-join them so a term and its value are not split across units."""
    out = []
    for b in blocks:
        prev = out[-1] if out else None
        if (prev and b["kind"] in ("list_item", "paragraph")
                and prev["kind"] in ("list_item", "paragraph")):
            rest = re.sub(r"^-\s+", "", b["text"])
            if (not re.search(r"[.:;?!)\"']$", prev["text"].strip())
                    and re.match(r"[a-z]", rest) and not re.match(r"[a-z][.)]\s", rest)):
                prev["text"] = prev["text"].rstrip() + " " + rest
                continue
        out.append(dict(b))
    return out


def build_units(md_text):
    """Return a list of units: {id, line, kind, text, context}.
    `text` is what the unit itself says; `context` is extra text carried for
    matching only (a table row carries its table's caption and header rows)."""
    md_text = md_text.replace("<!-- image -->", "")
    blocks = _merge_page_breaks(_blocks(md_text.splitlines()))
    units = []
    recent = []          # last few text blocks before a table = its caption
    for b in blocks:
        if b["kind"] == "table":
            caption = " / ".join(recent[-3:])
            headers = []
            data_seen = False
            for ln, row in b["rows"]:
                if re.fullmatch(r"\|?[\s:\-|]+\|?", row.strip()):
                    continue
                cells = _cells(row)
                # Docling repeats merged cells; de-duplicate consecutive repeats
                dedup = [c for k, c in enumerate(cells) if c and (k == 0 or c != cells[k - 1])]
                row_text = " | ".join(dedup)
                if not headers or (not data_seen and _is_header_row(cells)):
                    headers.append(row_text)
                    units.append({"line": ln, "kind": "table_header", "text": row_text,
                                  "context": caption})
                    continue
                data_seen = True
                units.append({"line": ln, "kind": "table_row", "text": row_text,
                              "context": (caption + " || " + " || ".join(headers)).strip(" |")})
            continue
        recent.append(b["text"][:150])
        if b["kind"] == "heading":
            units.append({"line": b["line"], "kind": "heading", "text": b["text"], "context": ""})
        elif b["kind"] == "list_item":
            units.append({"line": b["line"], "kind": "list_item", "text": b["text"], "context": ""})
        else:
            for sent in split_sentences(b["text"]):
                units.append({"line": b["line"], "kind": "sentence", "text": sent, "context": ""})
    for k, u in enumerate(units):
        u["id"] = k
    return units


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def compile_keywords(kw):
    macros = kw.get("hint_macros", {})

    def expand(h):
        return re.compile(macros[h] if h in macros else h)

    ge = kw.get("global_exclude", {})
    g = {
        "code_line": re.compile(ge["code_line_regex"]) if ge.get("code_line_regex") else None,
        "title_line": re.compile(ge["title_line_regex"]) if ge.get("title_line_regex") else None,
        "req_words": [term_regex(w) for w in ge.get("requirement_words", [])],
        "extra": [re.compile(p) for p in ge.get("extra_regex", [])],
    }
    xref = re.compile(kw["cross_ref_regex"]) if kw.get("cross_ref_regex") else None
    params = {}
    for name, p in kw["parameters"].items():
        params[name] = {
            "terms": [(t, term_regex(t)) for t in p["terms"]],
            "hints": [(h, expand(h)) for h in p.get("value_hints", [])],
            "exclude": [(e, term_regex(e)) for e in p.get("exclude", [])],
            "exclude_context": [(e, term_regex(e)) for e in p.get("exclude_context", [])],
            "xref": xref if p.get("cross_ref") else None,
            "descriptive": bool(p.get("descriptive")),
            "term_in_text": bool(p.get("term_in_unit_text", False)),
        }
    return g, params


def globally_excluded(norm_text, g):
    has_req = any(r.search(norm_text) for r in g["req_words"])
    if g["code_line"] and g["code_line"].search(norm_text) and not has_req:
        return "reference_line"
    if g["title_line"] and g["title_line"].search(norm_text) and not has_req:
        return "title_line"
    for r in g["extra"]:
        if r.search(norm_text):
            return "extra:" + r.pattern
    return None


def search(units, g, p):
    hits = []
    for u in units:
        # A bare heading ("Compaction of Concrete") states no requirement.
        if p["descriptive"] and u["kind"] == "heading":
            continue
        own = normalize(u["text"])
        full = normalize((u["context"] + " || " + u["text"]) if u["context"] else u["text"])
        if globally_excluded(own, g):
            continue
        term_space = own if p["term_in_text"] else full
        terms = [t for t, r in p["terms"] if r.search(term_space)]
        if not terms:
            continue
        if any(r.search(own) for _, r in p["exclude"]):
            continue
        if any(r.search(full) for _, r in p["exclude_context"]):
            continue
        # A table row may take its unit (mg/l, kg/m3) from the header, but the
        # row itself must hold a number - a header alone carries no value.
        hints = [h for h, r in p["hints"] if r.search(full)]
        if hints and not re.search(r"\d", own):
            hints = []
        # A requirement deferred to a table / IS code / the drawings counts as
        # a hit too (it tells the extractor where the value lives). Only prose:
        # "complying with IS 383" inside a table header is a label, not a deferral.
        if (p["xref"] is not None and u["kind"] in ("sentence", "list_item")
                and p["xref"].search(own)):
            hints.append("@cross_ref")
        if not p["descriptive"] and not hints:
            continue
        hits.append({"id": u["id"], "line": u["line"], "kind": u["kind"], "text": u["text"],
                     "context": u["context"], "terms": terms, "hints": hints})
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--keywords", required=True)
    ap.add_argument("--param", action="append")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    with open(args.doc, encoding="utf-8") as f:
        units = build_units(f.read())
    with open(args.keywords, encoding="utf-8") as f:
        g, params = compile_keywords(json.load(f))
    names = args.param or list(params)
    result = {n: search(units, g, params[n]) for n in names}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"n_units": len(units), "hits": result}, f, indent=1, ensure_ascii=False)
    for n in names:
        print(f"{n}: {len(result[n])} hits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
