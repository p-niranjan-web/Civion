import os
import sys
from groq import Groq

# Automatically load variables from .env file if present
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().lstrip("\ufeff"), v.strip().strip("'\""))

# Load environment variable for Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Model used for every LLM call (extraction agents + chat).
# Override with GROQ_MODEL in the environment / .env file if the account
# has access to a different model. The previous default
# ("llama-3.3-70b-versatile") was decommissioned by Groq and now returns
# HTTP 404 "model_not_found", which made every extraction return nothing.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY environment variable is not set. Ensure it is set before running inference.")

def get_groq_client():
    global GROQ_API_KEY
    if not GROQ_API_KEY:
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is missing. Cannot initialize client.")
    return Groq(api_key=GROQ_API_KEY)

