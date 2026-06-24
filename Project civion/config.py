import os
import sys
from groq import Groq

# Load environment variable for Groq API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY environment variable is not set. Ensure it is set before running inference.")

def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is missing. Cannot initialize client.")
    return Groq(api_key=GROQ_API_KEY)
