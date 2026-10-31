"""Specification PDF -> extraction JSON for the compliance engine (pipeline v4).

    PDF --(doc_prep: Docling, or the pre-converted demo Markdown)--> clean Markdown
        --> ONE Gemini call on the whole document (extraction_prompt.py)
        --> to_contract(): the JSON that auditor.run_civion_audit reads

The three aggregate grading tables are read by Gemini itself, cell by cell (no Python table
reader). History and measurements: experiments/pipeline_v4/REPORT_V4.md. The earlier Groq
pdfplumber parser is in git history (commit 81583db and before).
"""
import hashlib
import json
import os

import config
import doc_prep
import extraction_prompt as prompt
import gemini_client

# Bump when the prompt or the contract changes, so old cache files are not served.
PIPELINE_VERSION = "v4-gemini-cells-1"

FORMWORK_FIELDS = ["formwork_removal_hours", "formwork_removal_days", "formwork_span_m"]
MEMBERS = ["Beams", "Columns", "Slabs"]
CACHE_DIR = "downloads/cache"


def _is_empty(v):
    if isinstance(v, dict):
        return all(_is_empty(x) for x in v.values())
    return v is None or v == "" or v == []


def to_contract(parsed, exposure, concrete_type):
    """Gemini's answer -> the extraction contract auditor.py reads (field_info is dropped: nothing uses it)."""
    quotes_in = parsed.get("source_quotes") if isinstance(parsed.get("source_quotes"), dict) else {}
    remarks_in = parsed.get("remarks") if isinstance(parsed.get("remarks"), dict) else {}
    ext, quotes, remarks = {}, {}, {}
    for f in prompt.FIELDS:
        v = parsed.get(f)
        if f == "member_covers" and isinstance(v, dict):
            v = {m: v[m] for m in MEMBERS if not _is_empty(v.get(m))}
        ext[f] = None if _is_empty(v) else v
        if ext[f] is not None and quotes_in.get(f):
            quotes[f] = quotes_in[f]
        if remarks_in.get(f):
            remarks[f] = str(remarks_in[f])
    for f in FORMWORK_FIELDS:           # not in database.PARAMETERS: not asked for
        ext[f] = None
    ext["exposure"], ext["concrete_type"] = exposure, concrete_type
    quotes["exposure"] = f"Exposure condition determined outside the document: {exposure}"
    quotes["concrete_type"] = f"Concrete type determined outside the document: {concrete_type}"
    ext["cross_references"] = [x for x in (parsed.get("cross_references") or []) if isinstance(x, dict)]
    ext["source_quotes"] = quotes
    ext["remarks"] = remarks
    return ext


def _replay_path(source_name):
    return doc_prep.prebuilt_markdown_path(source_name).with_suffix(".response.json")


def _load_replay(source_name, exposure, concrete_type):
    """Demo mode: Gemini's saved answer for this document, so the demo makes no API call. Only used
    for the exposure / concrete type it was recorded with (the table row and column depend on them)."""
    if config.MD_SOURCE != "prebuilt":
        return None
    path = _replay_path(source_name)
    if not path.exists():
        return None
    saved = json.loads(path.read_text(encoding="utf-8"))
    if (saved.get("exposure"), saved.get("concrete_type")) != (exposure, concrete_type):
        return None
    print(f"[Demo] replaying saved Gemini answer {path.name} (no API call)")
    return saved["response"]


def _save_replay(source_name, exposure, concrete_type, parsed):
    if config.MD_SOURCE == "prebuilt":
        _replay_path(source_name).write_text(json.dumps(
            {"model": config.GEMINI_MODEL, "exposure": exposure, "concrete_type": concrete_type,
             "response": parsed}, indent=2, ensure_ascii=False), encoding="utf-8")


def _cache_path(pdf_path, source_name, exposure, concrete_type):
    key = "|".join([PIPELINE_VERSION, config.GEMINI_MODEL, config.MD_SOURCE,
                    doc_prep.source_fingerprint(pdf_path, source_name), exposure, concrete_type])
    return os.path.join(CACHE_DIR, hashlib.sha256(key.encode()).hexdigest() + ".json")


def parse_user_specification(pdf_path, detected_exposure=None, detected_concrete_type=None, source_name=None):
    """
    pdf_path: the uploaded PDF on disk. source_name: the name it was uploaded under (demo mode finds
    its pre-converted Markdown by this name).

    detected_exposure / detected_concrete_type: determined outside the document (exposure wizard /
    concrete-type picker). They tell Gemini which table row and column to read and are stamped onto
    the result. exposure is required. When no concrete type is given (UI: "Auto-detect") "Reinforced
    Concrete" is assumed and the traceability quote says so: the v4 prompt always receives a concrete
    type and was only tested that way.

    Results are cached (same document, exposure, concrete type, model, pipeline version). Returns the
    extraction JSON, or {"error": message} when the document or the model call fails.
    """
    exposure = (detected_exposure or "").strip()
    if not exposure:
        return {"error": "Exposure condition is required (the extraction reads the table row for it)."}
    concrete_type = (detected_concrete_type or "").strip()
    concrete_assumed = not concrete_type
    if concrete_assumed:
        concrete_type = "Reinforced Concrete"

    try:
        cache_file = _cache_path(pdf_path, source_name, exposure, concrete_type)
    except doc_prep.MarkdownNotAvailable as e:
        return {"error": str(e)}
    if os.path.exists(cache_file):
        print("Using cached extraction for this document / exposure / concrete type.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        parsed = _load_replay(source_name, exposure, concrete_type)
        if parsed is None:
            doc = doc_prep.prepare_document(pdf_path, source_name)
            parsed, _usage = gemini_client.call_json(prompt.build_system(exposure, concrete_type),
                                                     prompt.build_user(doc))
            _save_replay(source_name, exposure, concrete_type, parsed)
    except (doc_prep.MarkdownNotAvailable, RuntimeError, ValueError) as e:
        return {"error": str(e)}
    if not isinstance(parsed, dict):
        return {"error": "Gemini did not return a JSON object."}

    result = to_contract(parsed, exposure, concrete_type)
    if concrete_assumed:
        result["source_quotes"]["concrete_type"] = (
            "No concrete type selected; Reinforced Concrete assumed (not read from the document)")
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return result
