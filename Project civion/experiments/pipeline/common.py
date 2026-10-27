"""Shared helpers for the localization + extraction pipeline.

- Paths (this folder + the Civion project root on sys.path so config.py,
  auditor.py and database.py import unchanged).
- call_groq(): one JSON-mode Groq call that records the MEASURED token usage
  from the API's usage field, paces calls to stay under the free-tier
  tokens-per-minute cap and retries 429s with backoff.

The API key is never printed: config.get_groq_client() reads it and we only
ever log usage numbers and error messages.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUT_DIR = HERE / "output"
OUT_DIR.mkdir(exist_ok=True)

# Groq free tier is ~8,000 tokens/minute. Keep a margin below it.
TPM_BUDGET = 7000
WINDOW_S = 60.0

# (timestamp, total_tokens) of completed calls, for the sliding TPM window.
_recent = []
# Every call made in this process: name, MEASURED usage, wall time, retries.
CALL_LOG = []


# Some networks drop the large TLS ClientHello that OpenSSL 3.5 sends by default
# (post-quantum key share): the handshake to Groq times out while curl works.
# CIVION_CLASSIC_TLS=1 limits the handshake to one classic curve. Off by default.
CLASSIC_TLS = os.environ.get("CIVION_CLASSIC_TLS") == "1"


def _classic_tls_client():
    import ssl
    import httpx
    ctx = ssl.create_default_context()
    ctx.set_ecdh_curve("prime256v1")
    return httpx.Client(verify=ctx, timeout=120)


def est_tokens(text):
    """ESTIMATE only: chars / 4."""
    return len(text) // 4


def _wait_for_budget(expected_tokens):
    """Sleep until the last-60s token total plus this call fits the budget."""
    while True:
        now = time.time()
        _recent[:] = [(t, n) for (t, n) in _recent if now - t < WINDOW_S]
        used = sum(n for _, n in _recent)
        if not _recent or used + expected_tokens <= TPM_BUDGET:
            return
        # Wait until the oldest entry leaves the window.
        wait_s = WINDOW_S - (now - _recent[0][0]) + 0.5
        print(f"  [pace] {used} tokens used in last 60s; sleeping {wait_s:.1f}s")
        time.sleep(max(wait_s, 0.5))


def call_groq(name, system_prompt, user_prompt, expected_completion=1500, max_retries=5,
              reasoning_effort="low"):
    """Run one JSON-mode call. Returns (parsed_json_or_None, log_entry)."""
    from config import get_groq_client, GROQ_MODEL

    client = get_groq_client()
    if CLASSIC_TLS:
        client = client.with_options(http_client=_classic_tls_client())
    expected = est_tokens(system_prompt + user_prompt) + expected_completion
    entry = {"name": name, "model": GROQ_MODEL, "reasoning_effort": reasoning_effort, "prompt_tokens": None,
             "completion_tokens": None, "total_tokens": None, "retries": 0,
             "wall_s": None, "error": None, "est_prompt_tokens": est_tokens(system_prompt + user_prompt)}
    t0 = time.perf_counter()
    kwargs = dict(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
        temperature=0,
        seed=42,
        response_format={"type": "json_object"},
    )
    # gpt-oss models spend completion tokens on hidden reasoning; keep it
    # bounded so a call stays under the TPM cap. Dropped if rejected.
    if "gpt-oss" in GROQ_MODEL and reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    result = None
    for attempt in range(max_retries + 1):
        _wait_for_budget(expected)
        try:
            resp = client.chat.completions.create(**kwargs)
            u = resp.usage
            entry.update(prompt_tokens=u.prompt_tokens, completion_tokens=u.completion_tokens,
                         total_tokens=u.total_tokens)
            _recent.append((time.time(), u.total_tokens))
            content = resp.choices[0].message.content
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                entry["error"] = f"JSON decode failed: {e}"
                entry["raw"] = content[:2000]
            break
        except Exception as e:
            msg = str(e)
            if "reasoning_effort" in msg and "reasoning_effort" in kwargs:
                kwargs.pop("reasoning_effort")
                continue
            if ("429" in msg or "rate_limit" in msg) and attempt < max_retries:
                entry["retries"] += 1
                m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", msg)
                wait_s = (int(m.group(1) or 0) * 60 + float(m.group(2)) + 1.0) if m else 5.0 * 2 ** attempt
                print(f"  [429] {name}: retry {attempt + 1}/{max_retries} in {wait_s:.1f}s")
                # Count the budget as spent so the pacer also backs off.
                _recent.append((time.time(), TPM_BUDGET))
                time.sleep(wait_s)
                continue
            # Groq occasionally rejects a JSON-mode generation (HTTP 400
            # json_validate_failed, empty output). Retry it, without the fixed
            # seed so the retry is not the same sampling path; the failed
            # attempt's usage is not reported by the API.
            if "json_validate_failed" in msg and entry.get("json_retries", 0) < 2:
                entry["json_retries"] = entry.get("json_retries", 0) + 1
                kwargs.pop("seed", None)
                print(f"  [400 json_validate_failed] {name}: retry {entry['json_retries']}/2")
                continue
            entry["error"] = msg[:500]
            break
    entry["wall_s"] = round(time.perf_counter() - t0, 2)
    CALL_LOG.append(entry)
    print(f"  [call] {name}: prompt={entry['prompt_tokens']} completion={entry['completion_tokens']} "
          f"wall={entry['wall_s']}s retries={entry['retries']}" + (f" ERROR={entry['error']}" if entry["error"] else ""))
    return result, entry


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
