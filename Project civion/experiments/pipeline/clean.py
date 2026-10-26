"""STEP 1 - clean the Docling markdown.

Removes "<!-- image -->" markers, decodes HTML entities (&amp; -> &) and repeated page header/footer lines
(a whitespace/case-normalized line under 120 chars that appears 3+ times).
Table rows ("|...") are never treated as headers/footers. Digits are NOT
normalized away: doing so would make "TABLE - 4", "TABLE - 5", ... look like
one repeated line and delete every table caption.

Usage: python clean.py [input.md] [output.md]
"""
import html
import re
import sys
from collections import Counter
from pathlib import Path

from common import OUT_DIR, PROJECT_ROOT

DEFAULT_IN = PROJECT_ROOT / "experiments" / "parse_test" / "docling_output.md"

IMAGE_RE = re.compile(r"<!--\s*image\s*-->", re.I)
MIN_REPEATS = 3
MAX_LEN = 120


def normalize(line):
    return " ".join(line.split()).lower()


def is_protected(line):
    s = line.strip()
    return s.startswith("|") or not s


def clean(md):
    lines = html.unescape(IMAGE_RE.sub("", md)).splitlines()
    counts = Counter(normalize(l) for l in lines if not is_protected(l) and len(normalize(l)) < MAX_LEN)
    repeated = {k for k, n in counts.items() if n >= MIN_REPEATS}
    kept, removed = [], Counter()
    for l in lines:
        if not is_protected(l) and normalize(l) in repeated:
            removed[normalize(l)] += 1
            continue
        kept.append(l.rstrip())
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text, removed


def main(src=DEFAULT_IN, dst=OUT_DIR / "clean.md"):
    md = Path(src).read_text(encoding="utf-8")
    n_images = len(IMAGE_RE.findall(md))
    text, removed = clean(md)
    Path(dst).write_text(text, encoding="utf-8")
    stats = {"input_chars": len(md), "output_chars": len(text), "image_markers_removed": n_images,
             "repeated_lines_removed": dict(removed)}
    print(f"[clean] {len(md)} -> {len(text)} chars; {n_images} image markers; "
          f"{sum(removed.values())} header/footer lines ({len(removed)} distinct)")
    return stats


if __name__ == "__main__":
    main(*sys.argv[1:3])
