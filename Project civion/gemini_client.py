"""One JSON-mode Gemini call with retries (used by parser.py).

Adapted from experiments/pipeline_v4/gemini_call.py: same retry rules (429 / 5xx / dropped
connection, exponential backoff or the server's retryDelay, per-day quota is not retried), but
no experiment bookkeeping (call log, request/token pacing, daily budget).

The API key is read in config.py (environment or .env) and is never printed or logged.
"""
import json
import os
import re
import time

import config


def make_client():
    from google import genai
    from google.genai import types
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing (environment or Project civion/.env). Cannot call Gemini.")
    http = None
    # Some networks drop the large post-quantum TLS ClientHello; CIVION_CLASSIC_TLS=1 uses one classic curve.
    if os.environ.get("CIVION_CLASSIC_TLS") == "1":
        import ssl
        ctx = ssl.create_default_context()
        ctx.set_ecdh_curve("prime256v1")
        http = types.HttpOptions(client_args={"verify": ctx})
    return genai.Client(api_key=config.GEMINI_API_KEY, http_options=http)


def _retry_delay(msg, attempt):
    m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", msg)
    return float(m.group(1)) + 1.0 if m else min(10.0 * 2 ** attempt, 300.0)


def call_json(system_prompt, user_prompt, model=None, max_retries=5, max_output_tokens=32768):
    """Returns (parsed_json, usage). Raises RuntimeError when the call fails for good."""
    from google.genai import types

    model = model or config.GEMINI_MODEL
    client = make_client()
    cfg = types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json",
                                      max_output_tokens=max_output_tokens)
    t_all = time.perf_counter()
    last = "unknown error"
    for attempt in range(max_retries + 1):
        try:
            resp = client.models.generate_content(model=model, contents=user_prompt, config=cfg)
            u = resp.usage_metadata
            usage = {"model": model, "input_tokens": u.prompt_token_count, "output_tokens": u.candidates_token_count,
                     "reasoning_tokens": u.thoughts_token_count, "attempts": attempt + 1,
                     "wall_s": round(time.perf_counter() - t_all, 1)}
            print(f"[Gemini] {model}: in={usage['input_tokens']} out={usage['output_tokens']} "
                  f"reasoning={usage['reasoning_tokens']} attempts={usage['attempts']} wall={usage['wall_s']}s")
            try:
                return json.loads(resp.text or ""), usage
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Gemini returned invalid JSON: {e}")
        except RuntimeError:
            raise
        except Exception as e:
            msg = str(e)
            code = getattr(e, "code", None)
            last = msg[:300]
            rate_limited = code == 429 or "RESOURCE_EXHAUSTED" in msg
            per_day = rate_limited and re.search(r"PerDay|per day|RequestsPerDay", msg, re.I)
            # No HTTP code = the connection failed (e.g. "Server disconnected" after a long call).
            network = code is None and re.search(r"disconnect|timed? ?out|connect|reset|protocol", msg, re.I)
            retryable = rate_limited or network or (isinstance(code, int) and 500 <= code < 600)
            if per_day:
                raise RuntimeError(f"Gemini daily quota exhausted for {model}: {last}")
            if not retryable or attempt == max_retries:
                break
            wait = _retry_delay(msg, attempt)
            print(f"[Gemini] {code or 'network'} - retry {attempt + 1}/{max_retries} in {wait:.0f}s")
            time.sleep(wait)
    raise RuntimeError(f"Gemini call failed after {attempt + 1} attempt(s): {last}")
