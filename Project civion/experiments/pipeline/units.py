"""Split sections into small routing/extraction units (v2, Stage B input).

A unit is one of:
- a table (caption line + all "|" rows), always its own unit;
- a top-level lettered clause ("A. ...", "- B. ..."), or, when that clause
  is long, each of its numbered/lettered sub-clauses ("1.", "a.", "1)",
  "(a)") with the parent clause's first line kept in the heading path;
- leftover text, packed by lines.
Tiny pieces are merged into the following piece so units are not one-liners.
The patterns are generic spec-clause markers, not document-specific.
"""
import re

TOP_RE = re.compile(r"^(?:[-*]\s+)?[A-Z]\.\s")
SUB_RE = re.compile(r"^(?:[-*]\s+)?(?:\d{1,2}[.)]|[a-z][.)]|\(\w{1,3}\))\s")
MAX_UNIT = 1100     # chars; a clause longer than this is split at sub-clauses
HARD_MAX = 1800     # chars; anything longer is packed by lines
MIN_UNIT = 300      # chars; smaller pieces are merged into the next one


def _label(text, n=70):
    first = text.strip().splitlines()[0] if text.strip() else ""
    first = re.sub(r"^[-*]\s+", "", first)
    return first if len(first) <= n else first[:n - 3] + "..."


def _split_at(lines, rx):
    blocks, cur = [], []
    for l in lines:
        if rx.match(l.strip()) and cur:
            blocks.append(cur)
            cur = []
        cur.append(l)
    if cur:
        blocks.append(cur)
    return ["\n".join(b).strip() for b in blocks if "\n".join(b).strip()]


def _pack_lines(text, limit):
    out, cur = [], []
    for l in text.splitlines():
        if cur and len("\n".join(cur)) + len(l) > limit:
            out.append("\n".join(cur))
            cur = []
        cur.append(l)
    if cur:
        out.append("\n".join(cur))
    return out


def _merge_small(pieces):
    """pieces: [(extra_path, text)] -> merge tiny pieces into the next one."""
    out = []
    carry = None
    for path, text in pieces:
        if carry:
            path, text = carry[0], carry[1] + "\n" + text
            carry = None
        if len(text) < MIN_UNIT:
            carry = (path, text)
            continue
        out.append((path, text))
    if carry:
        if out:
            out[-1] = (out[-1][0], out[-1][1] + "\n" + carry[1])
        else:
            out.append(carry)
    return out


def split_text(text):
    """Return [(extra_path_list, text)] for a non-table text segment."""
    pieces = []
    for block in _split_at(text.splitlines(), TOP_RE):
        if len(block) <= MAX_UNIT:
            pieces.append(([], block))
            continue
        parent = _label(block)
        subs = _split_at(block.splitlines(), SUB_RE)
        for k, sub in enumerate(subs):
            extra = [] if k == 0 and TOP_RE.match(sub.strip()) else [parent]
            for part in (_pack_lines(sub, MAX_UNIT) if len(sub) > HARD_MAX else [sub]):
                pieces.append((extra, part))
    return _merge_small(pieces)


def section_units(section):
    """Units of one section, in document order."""
    lines = section["text"].splitlines()
    units = []
    seg = []
    tables = iter(section["tables"])

    def flush():
        txt = "\n".join(seg).strip()
        seg.clear()
        if txt:
            for extra, t in split_text(txt):
                units.append({"kind": "text", "heading_path": section["heading_path"] + extra, "text": t})

    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            # A short text run right above a table (e.g. a source note under
            # its caption) belongs with the table, not in its own unit.
            lead = "\n".join(seg).strip()
            if lead and len(lead) < MIN_UNIT:
                seg.clear()
            else:
                lead = ""
                flush()
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            t = next(tables, None)
            caption = (t or {}).get("caption") or "(no caption)"
            units.append({"kind": "table", "table_id": (t or {}).get("id"),
                          "heading_path": section["heading_path"] + [f"[TABLE] {caption}"],
                          "caption": caption, "text": (lead + "\n" if lead else "") + "\n".join(lines[i:j])})
            i = j
        else:
            seg.append(lines[i])
            i += 1
    flush()
    for n, u in enumerate(units, 1):
        u["id"] = f"{section['id']}.U{n}"
        u["section_id"] = section["id"]
    return units


def table_preview(text, n_rows=3, limit=400, cell=45):
    lead = [r for r in text.splitlines() if not r.lstrip().startswith("|")]
    rows = [r for r in text.splitlines()
            if r.lstrip().startswith("|") and not re.match(r"^\|[\s|:-]+\|$", r.strip())]
    out_rows = []
    for r in rows[:1 + n_rows]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        out_rows.append("| " + " | ".join(c if len(c) <= cell else c[:cell - 3] + "..." for c in cells) + " |")
    rows = lead + out_rows
    out = "\n".join(rows)
    return out if len(out) <= limit else out[:limit - 3] + "..."
