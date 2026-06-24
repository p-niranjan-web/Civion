import json
import pypdf
import hashlib
import os
from config import get_groq_client

def extract_text_from_pdf(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        raw_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text
        clean_text = " ".join(raw_text.split())
        if not clean_text:
            return None, "PDF contains no readable text."
        return clean_text, None
    except Exception as e:
        return None, f"Failed to read PDF: {str(e)}"

def run_agent(client, system_prompt, user_prompt):
    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
        print(f"❌ AI Extraction Error: {e}")
        return None

def get_file_hash(pdf_path):
    hasher = hashlib.sha256()
    with open(pdf_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def parse_user_specification(pdf_path):
    """
    Step 1: Check cache for deterministic results.
    Step 2: Extract raw text from PDF.
    Step 3: Sequential Multi-Agent Extraction Chain.
    Step 4: Merge results into unified structured JSON with source_quotes.
    """
    # ---------------------------------------------------------
    # CACHE CHECK
    # ---------------------------------------------------------
    file_hash = get_file_hash(pdf_path)
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
    # AGENT 1: Environmental & Geographical Limits
    # ---------------------------------------------------------
    prompt_env = f"""
    Extract environmental and geographical limits from the text.
    Return exact JSON structure:
    {{
      "exposure": ["Mild", "Moderate", "Severe", "Very Severe", "Extreme"],
      "freezing_thawing_exposure": (bool),
      "water_ph": (FLOAT),
      "soil_total_so3_percent": (FLOAT),
      "soil_extract_2_1_so3_gl": (FLOAT),
      "groundwater_so3_gl": (FLOAT),
      "source_quotes": {{
         "exposure": "exact quote from text",
         "freezing_thawing_exposure": "quote",
         "water_ph": "quote",
         "soil_total_so3_percent": "quote",
         "soil_extract_2_1_so3_gl": "quote",
         "groundwater_so3_gl": "quote"
      }}
    }}
    Text: {text_chunk}
    """
    env_data = run_agent(client, system_instruction, prompt_env) or {}

    # ---------------------------------------------------------
    # AGENT 2: Concrete Material Specs
    # ---------------------------------------------------------
    prompt_mat = f"""
    Extract concrete material specifications from the text.
    NOTE: Explicitly extract "concrete_type" exactly as "Plain Concrete" or "Reinforced Concrete". Do not use fallbacks.
    Return exact JSON structure:
    {{
      "concrete_type": ["Plain Concrete", "Reinforced Concrete"],
      "specified_grade": "String like M20",
      "cement_type": ["OPC", "PPC", "Mineral Admixture"],
      "specified_min_cement": (INT in kg/m3),
      "specified_max_cement": (INT in kg/m3),
      "specified_wc": (FLOAT),
      "specified_characteristic_strength": (INT),
      "specified_sigma": (INT),
      "mixing_time_minutes": (INT),
      "transport_time_minutes": (INT),
      "compaction_method": ["mechanical vibrator", "manual", "hand", "ramming"],
      "curing_days": (INT),
      "specified_slump_mm": (INT),
      "max_aggregate_size_mm": (INT),
      "total_volume_m3": (INT),
      "specified_sampling_sets": (INT),
      "sampling_cube_size_mm": (INT),
      "measured_chloride_content": (FLOAT),
      "measured_so3_percent": (FLOAT),
      "source_quotes": {{
         "concrete_type": "exact quote from text",
         "specified_grade": "quote",
         // add all keys here mapped to their exact quotes
      }}
    }}
    Ensure source_quotes contains a quote for every extracted parameter.
    Text: {text_chunk}
    """
    mat_data = run_agent(client, system_instruction, prompt_mat) or {}

    # ---------------------------------------------------------
    # AGENT 3: Member Structural Cover Rules
    # ---------------------------------------------------------
    prompt_struct = f"""
    Extract member structural cover rules from the text.
    Return exact JSON structure:
    {{
      "fire_resistance_rating": ["0.5hr", "1hr", "1.5hr", "2hr", "4hr"],
      "member_covers": {{
        "Beams": (INT in mm),
        "Columns": (INT in mm),
        "Slabs": (INT in mm)
      }},
      "source_quotes": {{
         "fire_resistance_rating": "exact quote from text",
         "member_covers": "quote"
      }}
    }}
    Text: {text_chunk}
    """
    struct_data = run_agent(client, system_instruction, prompt_struct) or {}

    # ---------------------------------------------------------
    # MERGE RESULTS
    # ---------------------------------------------------------
    merged_data = {}
    merged_quotes = {}
    
    for data in [env_data, mat_data, struct_data]:
        for k, v in data.items():
            if k == "source_quotes":
                merged_quotes.update(v)
            else:
                merged_data[k] = v
                
    merged_data["source_quotes"] = merged_quotes
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(merged_data, f)
        
    return merged_data
