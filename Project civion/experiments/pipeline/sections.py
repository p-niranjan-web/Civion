"""STEP 2 - split clean.md into sections and tables.

Sections start at markdown headings. Docling often emits every heading at the
same level ("##"), so when all headings share one level the hierarchy is
inferred from common spec numbering (PART n > 1.2 > 1.2.3 > A. > 1.), and an
unnumbered heading becomes a child of the last numbered one. A heading with
no body that is directly followed by another heading and is itself
unnumbered (e.g. "TABLE - 5" + its title on the next line) is merged with
that next heading into one "A / B" heading.

A table is a run of consecutive lines starting with "|". Its caption is built
from the title-like lines directly above it (a heading, a line starting with
"Table", or a short line not ending in sentence punctuation). A sentence that
only mentions a table has no "|" rows after it and is never a table.

Outputs: sections.json and outline.txt.
Usage: python sections.py [clean.md]
"""
import re
import sys
from pathlib import Path

from common import OUT_DIR, write_json

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBERED_PATTERNS = [
    (re.compile(r"^PART\s+\d+\b", re.I), lambda m: 1),
    (re.compile(r"^(\d+(?:\.\d+)+)\.?\s"), lambda m: 1 + m.group(1).count(".")),
    (re.compile(r"^[A-Z]\.\s"), None),     # A. B. C. -> one below last numeric
    (re.compile(r"^\d+\.\s"), None),       # 7.       -> one below last letter
]


def heading_number_kind(text):
    """Return (kind, depth) for numbered headings, or (None, None)."""
    for i, (rx, depth_fn) in enumerate(NUMBERED_PATTERNS):
        m = rx.match(text)
        if m:
            return i, (depth_fn(m) if depth_fn else None)
    return None, None


def is_title_like(line):
    s = line.strip()
    if not s or s.startswith("|"):
        return False
    if HEADING_RE.match(s):
        return True
    if re.match(r"^\[?\s*table\b", s, re.I):
        return True
    return len(s) <= 100 and not s.endswith((".", ":", ";", ",")) and not re.match(r"^[-*]\s", s)


def find_headings(lines):
    """Return [(line_idx, md_level, text, merged_line_idxs)] with merging applied."""
    raw = [(i, len(m.group(1)), m.group(2).strip()) for i, l in enumerate(lines)
           if (m := HEADING_RE.match(l))]
    merged = []
    k = 0
    while k < len(raw):
        i, lvl, text = raw[k]
        idxs = [i]
        # Merge unnumbered, body-less headings into the following heading.
        while k + 1 < len(raw):
            nxt_i = raw[k + 1][0]
            body_between = any(lines[j].strip() for j in range(idxs[-1] + 1, nxt_i))
            if body_between or heading_number_kind(text.split(" / ")[-1])[0] is not None:
                break
            k += 1
            text = f"{text} / {raw[k][2]}"
            idxs.append(raw[k][0])
        merged.append((i, lvl, text, idxs))
        k += 1
    return merged


def assign_levels(headings):
    md_levels = {h[1] for h in headings}
    if len(md_levels) > 1:
        return [h[1] for h in headings]
    levels = []
    last_numeric = 1      # depth of last PART / n.n heading
    last_letter = None    # depth of last "A." heading
    last_numbered = 0     # depth of last numbered heading of any kind
    for _, _, text, _ in headings:
        kind, depth = heading_number_kind(text)
        if kind in (0, 1):
            last_numeric, last_letter = depth, None
            lvl = depth
        elif kind == 2:
            lvl = last_numeric + 1
            last_letter = lvl
        elif kind == 3:
            lvl = (last_letter or last_numeric) + 1
        else:
            lvl = last_numbered + 1 if last_numbered else 1
            levels.append(lvl)
            continue
        last_numbered = lvl
        levels.append(lvl)
    return levels


def find_tables(lines, body_start, body_end, heading_text):
    """Tables (runs of '|' lines) inside lines[body_start:body_end]."""
    tables = []
    j = body_start
    while j < body_end:
        if lines[j].lstrip().startswith("|"):
            start = j
            while j < body_end and lines[j].lstrip().startswith("|"):
                j += 1
            end = j
            # Caption: consecutive title-like lines directly above the table.
            parts = []
            p = start - 1
            reached_heading = True
            while p >= body_start:
                if not lines[p].strip():
                    p -= 1
                    continue
                if is_title_like(lines[p]) and len(parts) < 3:
                    parts.insert(0, lines[p].strip())
                    p -= 1
                    continue
                reached_heading = False
                break
            if reached_heading and len(parts) < 3:
                parts.insert(0, heading_text)
            tables.append({"line_start": start, "line_end": end,
                           "caption": " / ".join(parts) if parts else None})
        else:
            j += 1
    return tables


def build(clean_md):
    lines = clean_md.splitlines()
    offsets = [0]
    for l in lines:
        offsets.append(offsets[-1] + len(l) + 1)

    headings = find_headings(lines)
    levels = assign_levels(headings)

    sections = []
    if headings and any(l.strip() for l in lines[:headings[0][0]]):
        headings = [(0, 0, "(preamble)", [])] + headings
        levels = [0] + levels
    stack = []  # (level, heading)
    for n, ((i, _, text, idxs), lvl) in enumerate(zip(headings, levels)):
        body_start = (idxs[-1] + 1) if idxs else 0
        body_end = headings[n + 1][0] if n + 1 < len(headings) else len(lines)
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        path = [h for _, h in stack] + [text]
        stack.append((lvl, text))
        sid = f"S{n:03d}"
        tables = []
        for t_no, t in enumerate(find_tables(lines, body_start, body_end, text), 1):
            ttext = "\n".join(lines[t["line_start"]:t["line_end"]])
            tables.append({
                "id": f"{sid}.T{t_no}",
                "caption": t["caption"],
                "header": [c.strip() for c in lines[t["line_start"]].strip().strip("|").split("|")],
                "n_rows": t["line_end"] - t["line_start"],
                "char_span": [offsets[t["line_start"]], offsets[t["line_end"]]],
                "text": ttext,
            })
        sections.append({
            "id": sid,
            "heading": text,
            "level": lvl,
            "heading_path": path,
            "char_span": [offsets[i], offsets[body_end]],
            "text": "\n".join(lines[body_start:body_end]).strip(),
            "tables": tables,
        })
    return sections


def table_label(t, section_heading):
    cols = " | ".join(c for c in t["header"] if c)[:120]
    if not t["caption"]:
        return f"(no caption; columns: {cols})"
    if t["caption"] == section_heading:
        # Caption is only the enclosing heading: add the columns so the
        # outline still says what the table holds.
        return f"{t['caption']} (columns: {cols})"
    return t["caption"]


def outline_text(sections):
    out = []
    for s in sections:
        indent = "  " * max(s["level"] - 1, 0)
        out.append(f"{s['id']} {indent}{s['heading']}")
        for t in s["tables"]:
            out.append(f"{t['id']} {indent}  [TABLE] {table_label(t, s['heading'])}")
    return "\n".join(out) + "\n"


def main(src=None, out_dir=OUT_DIR):
    clean_md = Path(src or out_dir / "clean.md").read_text(encoding="utf-8")
    sections = build(clean_md)
    write_json(out_dir / "sections.json", sections)
    (out_dir / "outline.txt").write_text(outline_text(sections), encoding="utf-8")
    n_tables = sum(len(s["tables"]) for s in sections)
    print(f"[sections] {len(sections)} sections, {n_tables} tables")
    return {"sections": len(sections), "tables": n_tables}


if __name__ == "__main__":
    main(*sys.argv[1:2])
