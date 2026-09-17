import json
import re
import time
import pdfplumber
import hashlib
import os
from config import get_groq_client, GROQ_MODEL

def extract_text_from_pdf(pdf_path):
    """Extract text page-by-page, keeping table rows intact.

    pypdf's extract_text() plus " ".join(raw_text.split()) used to flatten
    every page into one run-on string, destroying whitespace-aligned table
    structure entirely - a spec's requirements table (e.g. IS 456 Table 1
    water limits) became an unparseable jumble before it ever reached the
    LLM. pdfplumber keeps line breaks in normal text and additionally
    extracts each table's rows explicitly, so both the narrative text and
    a clean "cell | cell | cell" rendering of every table are preserved.
    """
    try:
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    parts.append(page_text)
                for table in page.extract_tables():
                    rows = []
                    for row in table:
                        cells = [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
                        if any(cells):
                            rows.append(" | ".join(cells))
                    if rows:
                        parts.append("TABLE:\n" + "\n".join(rows))
        raw_text = "\n".join(parts)
        # Collapse only the whitespace within each line - keep line breaks so
        # table rows and paragraphs stay distinguishable from one another.
        clean_text = "\n".join(" ".join(line.split()) for line in raw_text.splitlines() if line.strip())
        if not clean_text:
            return None, "PDF contains no readable text."
        return clean_text, None
    except Exception as e:
        return None, f"Failed to read PDF: {str(e)}"

def run_agent(client, system_prompt, user_prompt, max_retries=4):
    """Call the model and parse its JSON reply.

    Retries on transient rate-limit (HTTP 429) responses with a short
    backoff - the free Groq tier caps tokens-per-minute, so a burst of
    calls (e.g. an audit right after a chat turn) can still be throttled
    even though the extraction itself is now a single call.
    """
    for attempt in range(max_retries + 1):
        try:
            chat_completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                seed=42,
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            msg = str(e)
            is_rate_limit = "429" in msg or "rate_limit" in msg
            if is_rate_limit and attempt < max_retries:
                m = re.search(r"try again in ([\d.]+)s", msg)
                wait_s = float(m.group(1)) + 0.5 if m else 2.0 * (attempt + 1)
                print(f"[AI Extraction] rate limited, retrying in {wait_s:.1f}s "
                      f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_s)
                continue
            # Plain ASCII only - a non-ASCII marker here raises UnicodeEncodeError
            # on the default Windows console and hides the real error.
            print(f"[AI Extraction Error] {e}")
            return None

def get_file_hash(pdf_path):
    hasher = hashlib.sha256()
    with open(pdf_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def parse_user_specification(pdf_path, detected_exposure=None, detected_concrete_type=None):
    """
    Step 1: Check cache for deterministic results.
    Step 2: Extract raw text from PDF.
    Step 3: Single-pass structured extraction (one LLM call).
    Step 4: Stamp externally-determined context onto the JSON.

    A single call is used rather than three sequential agents: on the Groq
    free tier (8000 tokens/minute) three back-to-back calls tripped the
    rate limiter and each retry added ~5-45s, so Spec Doc 3 took 1-2 min.
    One call keeps the whole extraction well under the TPM cap and returns
    in a few seconds.

    detected_exposure: optional environmental exposure condition already
    determined outside the document (user-selected or derived via the
    exposure questionnaire). When provided, the extraction agent is told
    to fetch only the values that apply to that exposure case, and the
    value is stamped onto the final JSON used for the compliance check.

    detected_concrete_type: optional "Plain Concrete" / "Reinforced Concrete"
    hint. Some specs give requirements only as a table keyed by both exposure
    class and concrete type; this tells the agents which column to read. When
    omitted, the agents infer the applicable concrete type from the document.
    """
    if isinstance(detected_concrete_type, str):
        detected_concrete_type = detected_concrete_type.strip() or None

    # ---------------------------------------------------------
    # CACHE CHECK
    # ---------------------------------------------------------
    file_hash = get_file_hash(pdf_path)
    if detected_exposure:
        # Fold the detected exposure into the cache key so re-running the
        # same document with a different exposure type is not served a
        # stale extraction.
        file_hash = hashlib.sha256(f"{file_hash}:{detected_exposure}".encode()).hexdigest()
    if detected_concrete_type:
        file_hash = hashlib.sha256(f"{file_hash}:{detected_concrete_type}".encode()).hexdigest()
    cache_dir = "downloads/cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{file_hash}.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            print("🚀 Using cached parser results for deterministic output.")
            return json.load(f)
            
    clean_text, error = extract_text_from_pdf(pdf_path)
    if error:
        return {"error": error}
    
    client = get_groq_client()
    text_chunk = clean_text[:12000]

    system_instruction = "You are a civil engineering parser. Output STRICTLY valid JSON. Do NOT invent values. If missing, return null."

    # ---------------------------------------------------------
    # DETECTED EXPOSURE CONTEXT (additive instruction only)
    # ---------------------------------------------------------
    exposure_context = ""
    if detected_exposure:
        exposure_context = (
            f"\n    IMPORTANT CONTEXT: The applicable environmental exposure condition for this "
            f"structure has ALREADY been determined externally to be \"{detected_exposure}\". "
            f"The document may describe specifications for a single exposure condition, or it may "
            f"list several different exposure cases/scenarios. If more than one exposure case is "
            f"present, extract ONLY the values that apply to the \"{detected_exposure}\" exposure "
            f"case and ignore the values given for the other exposure cases. Always set the "
            f"\"exposure\" field to \"{detected_exposure}\".\n"
            f"    TABLE RESOLUTION: Some documents do not state a single number but instead give a "
            f"REQUIREMENTS TABLE whose rows are exposure classes (Mild / Moderate / Severe / Very "
            f"Severe / Extreme) and whose columns are the concrete type (Plain Concrete vs "
            f"Reinforced Concrete) and/or the parameter (minimum cement content, maximum "
            f"water-cement ratio, minimum grade, nominal cover, sampling frequency, etc.). "
            f"When a value is only available from such a table, you MUST look it up: pick the row "
            f"for the \"{detected_exposure}\" exposure class"
            + (f" and the \"{detected_concrete_type}\" column" if detected_concrete_type else " and the applicable concrete-type column")
            + f", then return that cell's number as the field value. Do NOT leave the field null "
            f"when the number can be read from a table row - resolve it. Put the exact table "
            f"row/cell text in source_quotes.\n"
        )
    
    # ---------------------------------------------------------
    # CONCRETE-TYPE HINT (which table column to read)
    # ---------------------------------------------------------
    if detected_concrete_type:
        concrete_type_hint = (
            f' The applicable concrete type for this structure is "{detected_concrete_type}" - '
            f'set "concrete_type" to that and read every exposure/concrete-type table using that column.'
        )
    else:
        concrete_type_hint = (
            ' If the document names both plain and reinforced concrete, choose the one it says is '
            'used for the actual structural members (e.g. "reinforced cement concrete shall be used '
            'typically at all locations" => "Reinforced Concrete").'
        )

    # ---------------------------------------------------------
    # SINGLE-PASS EXTRACTION (one call - see docstring)
    # ---------------------------------------------------------
    prompt_all = f"""
    Extract the concrete specification below into ONE JSON object.
    Rules: use only values stated (or table-resolvable) in the text; if a value
    is missing return null; never invent numbers.
    For "concrete_type" return exactly "Plain Concrete" or "Reinforced Concrete" as a single string.{concrete_type_hint}
    The "water_organic_mg_l", "water_inorganic_mg_l", "water_sulphates_mg_l",
    "water_chlorides_mg_l" and "water_suspended_matter_mg_l" fields come from a
    "PERMISSIBLE LIMITS FOR SOLIDS (IN WATER)" style table (mixing/curing water
    quality per IS 456 Table 1) - do NOT confuse this with the soil/groundwater
    sulphate-attack fields above (soil_total_so3_percent, soil_extract_2_1_so3_gl,
    groundwater_so3_gl), which come from a different table.
    {exposure_context}
    Return exactly this JSON structure (same keys, correct types):
    {{
      "exposure": "Mild|Moderate|Severe|Very Severe|Extreme",
      "freezing_thawing_exposure": bool,
      "water_ph": float,
      "soil_total_so3_percent": float,
      "soil_extract_2_1_so3_gl": float,
      "groundwater_so3_gl": float,
      "concrete_type": "Plain Concrete|Reinforced Concrete",
      "specified_grade": "string like M20",
      "cement_type": "OPC|PPC|PSC|SRC|Mineral Admixture",
      "specified_min_cement": int,
      "specified_max_cement": int,
      "specified_wc": float,
      "specified_characteristic_strength": int,
      "specified_sigma": int,
      "mixing_time_minutes": int,
      "transport_time_minutes": int,
      "compaction_method": "mechanical vibrator|manual|hand|ramming",
      "curing_days": int,
      "specified_slump_mm": int,
      "total_volume_m3": int,
      "specified_sampling_sets": int,
      "sampling_cube_size_mm": int,
      "measured_chloride_content": float,
      "measured_so3_percent": float,
      "fire_resistance_rating": "0.5hr|1hr|1.5hr|2hr|4hr",
      "member_covers": {{ "Beams": int, "Columns": int, "Slabs": int }},
      "water_organic_mg_l": float,
      "water_inorganic_mg_l": float,
      "water_sulphates_mg_l": float,
      "water_chlorides_mg_l": float,
      "water_suspended_matter_mg_l": float,
      "formwork_removal_hours": {{ "Walls_Columns": float }},
      "formwork_removal_days": {{ "Slabs": float, "Beam_Soffit": float, "Props_Under_Slabs": float, "Props_Under_Beams_Arches": float }},
      "formwork_span_m": {{ "Props_Under_Slabs": float, "Props_Under_Beams_Arches": float }},
      "cross_references": [ {{ "parameter": "string - which requirement is being deferred, e.g. coarse_aggregate_grading", "referenced_code": "string like 'IS 383'", "source_quote": "exact quote from text" }} ],
      "source_quotes": {{ "<field>": "exact quote from text for every non-null field above" }}
    }}
    CROSS-REFERENCES: A spec may state a requirement not as a number but by
    deferring it to another IS code (e.g. "Grading of coarse aggregate shall
    conform to the requirements of IS 383."). This is NOT missing data - do
    NOT return null for it and do NOT treat it as a failure. Instead add one
    entry to "cross_references" per such statement, naming the parameter it
    concerns, the exact code referenced (e.g. "IS 383"), and the exact quote.
    If there are no such deferrals, return an empty list.
    Text: {text_chunk}
    """
    merged_data = run_agent(client, system_instruction, prompt_all) or {}
    if not isinstance(merged_data.get("source_quotes"), dict):
        merged_data["source_quotes"] = {}
    if not isinstance(merged_data.get("cross_references"), list):
        merged_data["cross_references"] = []

    # ---------------------------------------------------------
    # STAMP DETECTED EXPOSURE ONTO THE FINAL JSON
    # (this JSON is consumed by the downstream compliance check)
    # ---------------------------------------------------------
    if detected_exposure:
        merged_data["exposure"] = detected_exposure
        if not merged_data["source_quotes"].get("exposure"):
            merged_data["source_quotes"]["exposure"] = (
                f"Exposure condition determined outside the document: {detected_exposure}"
            )

    if detected_concrete_type:
        merged_data["concrete_type"] = detected_concrete_type
        if not merged_data["source_quotes"].get("concrete_type"):
            merged_data["source_quotes"]["concrete_type"] = (
                f"Concrete type determined outside the document: {detected_concrete_type}"
            )

    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(merged_data, f)
        
    return merged_data
