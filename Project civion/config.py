import os
import sys
from groq import Groq

# Automatically load variables from .env file if present
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Load environment variable for Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY environment variable is not set. Ensure it is set before running inference.")

def get_groq_client():
    global GROQ_API_KEY
    if not GROQ_API_KEY:
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is missing. Cannot initialize client.")
    return Groq(api_key=GROQ_API_KEY)

