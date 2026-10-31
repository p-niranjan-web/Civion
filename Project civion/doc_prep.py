"""PDF -> clean Markdown for the extraction call.

Two ways to get the Markdown (config.MD_SOURCE / CIVION_MD_SOURCE):
  prebuilt - demo mode: demo_md/<uploaded file name>.md, converted once beforehand.
             Docling is not imported and not run.
  docling  - normal mode: the uploaded PDF is converted with Docling (minutes per document).

The Markdown is then cleaned exactly as in the v4 experiments (experiments/pipeline/clean.py and
run_v4.prepare_doc): image markers and HTML entities removed, repeated page headers/footers
dropped, Docling's table padding squeezed. No LLM is involved.
"""
import html
import re
from collections import Counter
from pathlib import Path

import config

DEMO_MD_DIR = Path(__file__).resolve().parent / "demo_md"

IMAGE_RE = re.compile(r"<!--\s*image\s*-->", re.I)
MIN_REPEATS = 3
MAX_LEN = 120


class MarkdownNotAvailable(Exception):
    pass


def _normalize(line):
    return " ".join(line.split()).lower()


def _is_protected(line):
    s = line.strip()
    return s.startswith("|") or not s


def clean(md):
    """Remove image markers, decode entities, drop repeated page header/footer lines (3+ copies, under
    120 chars). Table rows are never treated as headers/footers; digits are not normalized away
    (else every "TABLE - n" caption would look like one repeated line)."""
    lines = html.unescape(IMAGE_RE.sub("", md)).splitlines()
    counts = Counter(_normalize(l) for l in lines if not _is_protected(l) and len(_normalize(l)) < MAX_LEN)
    repeated = {k for k, n in counts.items() if n >= MIN_REPEATS}
    kept = [l.rstrip() for l in lines if _is_protected(l) or _normalize(l) not in repeated]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip() + "\n"
    return text


def squeeze_tables(text):
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            line = re.sub(r"-{3,}", "---", re.sub(r" {2,}", " ", line))
        out.append(line)
    return "\n".join(out) + "\n"


def prebuilt_markdown_path(source_name):
    return DEMO_MD_DIR / (Path(source_name or "").stem + ".md")


def source_fingerprint(pdf_path, source_name=None):
    """What the extraction depends on, for the cache key: the converted Markdown in demo mode,
    otherwise the PDF itself (so a cache hit skips the slow Docling conversion)."""
    import hashlib
    if config.MD_SOURCE == "prebuilt":
        md_path = prebuilt_markdown_path(source_name)
        if not source_name or not md_path.exists():
            raise MarkdownNotAvailable(_missing_message(source_name))
        return hashlib.sha256(md_path.read_bytes()).hexdigest()
    return hashlib.sha256(Path(pdf_path).read_bytes()).hexdigest()


def _missing_message(source_name):
    return (f"Demo mode (CIVION_MD_SOURCE=prebuilt) has no converted Markdown for '{source_name}'. "
            f"Expected: demo_md/{Path(source_name or '').stem}.md")


def convert_with_docling(pdf_path):
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise MarkdownNotAvailable(
            "Docling is not installed in this Python environment (pip install docling). "
            "Or set CIVION_MD_SOURCE=prebuilt to use a pre-converted file from demo_md/.")
    print("[Docling] converting PDF to Markdown - this takes minutes ...")
    return DocumentConverter().convert(str(pdf_path)).document.export_to_markdown()


def get_markdown(pdf_path, source_name=None):
    """Raw Markdown of the uploaded PDF. `source_name` is the name the user uploaded it under."""
    if config.MD_SOURCE == "prebuilt":
        md_path = prebuilt_markdown_path(source_name)
        if not source_name or not md_path.exists():
            raise MarkdownNotAvailable(_missing_message(source_name))
        print(f"[Demo] using pre-converted Markdown {md_path.name} (Docling skipped)")
        return md_path.read_text(encoding="utf-8")
    if config.MD_SOURCE == "docling":
        return convert_with_docling(pdf_path)
    raise MarkdownNotAvailable(f"Unknown CIVION_MD_SOURCE '{config.MD_SOURCE}' (use 'prebuilt' or 'docling').")


def prepare_document(pdf_path, source_name=None):
    return squeeze_tables(clean(get_markdown(pdf_path, source_name)))
