"""Gemini calls for v4: key loading, model config, rate limiter, retries, call log.

- The key is read from GEMINI_API_KEY (environment or "Project civion/.env").
  It is never printed, logged or written anywhere.
- Model IDs come from models_config.json (written by pick_models.py).
- Client-side limiter per model: requests/min and input tokens/min in a
  sliding 60 s window, seeded from call_log.jsonl so separate runs share it.
- 429 / 5xx are retried with exponential backoff (or the server's retryDelay);
  a per-day quota 429 is not retried.
- EVERY attempt is one line in call_log.jsonl: timestamp, model, input /
  output / reasoning tokens from the API's usage_metadata, wall time, status.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
PIPELINE_V2 = HERE.parent / "pipeline"
for p in (PROJECT_ROOT, PIPELINE_V2):
    if str(p) not in sys.path:
        sys.path.append(str(p))

ENV_FILE = PROJECT_ROOT / ".env"
CONFIG_FILE = HERE / "models_config.json"
CALL_LOG_FILE = HERE / "call_log.jsonl"
WINDOW_S = 60.0


def load_key():
    if not os.environ.get("GEMINI_API_KEY") and ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            k, sep, v = line.strip().partition("=")
            if sep and k.strip().lstrip("﻿") == "GEMINI_API_KEY":
                os.environ["GEMINI_API_KEY"] = v.strip().strip("'\"")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(f"GEMINI_API_KEY is not set (environment or {ENV_FILE}).")
    return key


def load_config():
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def model_id(role):
    """role "main" or "lite" -> model id from models_config.json."""
    return load_config()[role]["id"]


def limits_for(model):
    for role in ("main", "lite"):
        c = load_config()[role]
        if c["id"] == model:
            return c["limits"]
    return {"rpm": 5, "tpm": 250_000, "rpd": 20}


def make_client():
    from google import genai
    from google.genai import types
    http = None
    # Same workaround as experiments/pipeline/common.py: some networks drop the
    # large post-quantum TLS ClientHello; CIVION_CLASSIC_TLS=1 uses one classic curve.
    if os.environ.get("CIVION_CLASSIC_TLS") == "1":
        import ssl
        ctx = ssl.create_default_context()
        ctx.set_ecdh_curve("prime256v1")
        http = types.HttpOptions(client_args={"verify": ctx})
    return genai.Client(api_key=load_key(), http_options=http)


# ---------------------------------------------------------------------
# Call log and budget
# ---------------------------------------------------------------------
def read_log():
    if not CALL_LOG_FILE.exists():
        return []
    out = []
    for line in CALL_LOG_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def append_log(entry):
    with open(CALL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def quota_day_start():
    """Gemini per-day quotas reset at midnight Pacific time."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
    except Exception:          # no tz database on this machine: fixed UTC-8
        tz = timezone(timedelta(hours=-8))
    now = datetime.now(tz)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def used_today(model):
    """Requests to `model` since the last quota reset. 429 and 5xx answers are not
    counted (rejected before the model ran, e.g. 503 "high demand"); every other
    attempt is. If this undercounts, the server's per-day 429 stops the run."""
    start = quota_day_start()
    return sum(1 for e in read_log() if e.get("model") == model
               and not (e.get("status") == "429" or str(e.get("status", "")).startswith("5"))
               and datetime.fromisoformat(e["ts"]) >= start)


def remaining_today(model):
    return limits_for(model)["rpd"] - used_today(model)


def _wait_for_slot(model, est_input):
    lim = limits_for(model)
    while True:
        now = time.time()
        recent = [e for e in read_log() if e.get("model") == model
                  and now - datetime.fromisoformat(e["ts"]).timestamp() < WINDOW_S]
        n_req = len(recent)
        n_tok = sum((e.get("input_tokens") or e.get("est_input_tokens") or 0) for e in recent)
        if n_req < lim["rpm"] and n_tok + est_input <= lim["tpm"]:
            return
        oldest = min(datetime.fromisoformat(e["ts"]).timestamp() for e in recent)
        wait = max(WINDOW_S - (now - oldest) + 0.5, 0.5)
        print(f"  [pace] {model}: {n_req} req / {n_tok} input tokens in last 60s; sleeping {wait:.1f}s")
        time.sleep(wait)


def _retry_delay(msg, attempt):
    m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", msg)
    return float(m.group(1)) + 1.0 if m else min(10.0 * 2 ** attempt, 300.0)


def call_gemini(name, model, system_prompt, user_prompt, max_retries=5, max_output_tokens=32768,
                temperature=None, thinking=None):
    """One JSON-mode call. Returns (parsed_json_or_None, summary).
    `thinking`: None = model default; else a dict for types.ThinkingConfig."""
    from google.genai import types

    client = make_client()
    est_input = (len(system_prompt) + len(user_prompt)) // 4
    cfg = dict(system_instruction=system_prompt, response_mime_type="application/json",
               max_output_tokens=max_output_tokens)
    if temperature is not None:
        cfg["temperature"] = temperature
    if thinking:
        cfg["thinking_config"] = types.ThinkingConfig(**thinking)
    summary = {"name": name, "model": model, "attempts": 0, "retries": 0, "input_tokens": None,
               "output_tokens": None, "reasoning_tokens": None, "total_tokens": None,
               "wall_s": None, "status": None, "error": None}
    t_all = time.perf_counter()
    result = None
    for attempt in range(max_retries + 1):
        _wait_for_slot(model, est_input)
        summary["attempts"] += 1
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "name": name, "model": model,
                 "attempt": attempt + 1, "est_input_tokens": est_input}
        t0 = time.perf_counter()
        try:
            resp = client.models.generate_content(model=model, contents=user_prompt,
                                                  config=types.GenerateContentConfig(**cfg))
            u = resp.usage_metadata
            cand = (resp.candidates or [None])[0]
            entry.update(status="ok", input_tokens=u.prompt_token_count, output_tokens=u.candidates_token_count,
                         reasoning_tokens=u.thoughts_token_count, total_tokens=u.total_token_count,
                         finish_reason=str(getattr(cand, "finish_reason", None)),
                         wall_s=round(time.perf_counter() - t0, 2))
            text = resp.text or ""
            try:
                result = json.loads(text)
            except json.JSONDecodeError as e:
                entry.update(status="bad_json", error=f"JSON decode failed: {e}")
                summary["raw"] = text[:4000]
            append_log(entry)
            for k in ("input_tokens", "output_tokens", "reasoning_tokens", "total_tokens", "status", "error"):
                summary[k] = entry.get(k)
            summary["finish_reason"] = entry["finish_reason"]
            summary["ok_attempt_wall_s"] = entry["wall_s"]      # this attempt only; wall_s also holds retries + backoff
            break
        except Exception as e:
            msg = str(e)
            code = getattr(e, "code", None)
            status = "429" if code == 429 or "RESOURCE_EXHAUSTED" in msg else str(code or "error")
            entry.update(status=status, error=msg[:500], wall_s=round(time.perf_counter() - t0, 2))
            append_log(entry)
            summary.update(status=status, error=msg[:500])
            per_day = status == "429" and re.search(r"PerDay|per day|RequestsPerDay", msg, re.I)
            # No HTTP code = the connection failed (e.g. "Server disconnected without
            # sending a response" after a long thinking call): retried like a 5xx.
            network = code is None and re.search(r"disconnect|timed? ?out|connect|reset|protocol", msg, re.I)
            if network:
                status = entry["status"] = "network"
                summary["status"] = status
            retryable = status in ("429", "network") or (str(code).startswith("5") if code else False)
            if per_day or not retryable or attempt == max_retries:
                if per_day:
                    print(f"  [429] {name}: per-day quota exhausted for {model}; not retrying")
                break
            wait = _retry_delay(msg, attempt)
            summary["retries"] += 1
            print(f"  [{status}] {name}: retry {attempt + 1}/{max_retries} in {wait:.1f}s")
            time.sleep(wait)
    summary["wall_s"] = round(time.perf_counter() - t_all, 2)
    print(f"  [call] {name} {model}: in={summary['input_tokens']} out={summary['output_tokens']} "
          f"reasoning={summary['reasoning_tokens']} wall={summary['wall_s']}s status={summary['status']}")
    return result, summary
