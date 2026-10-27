"""List the Gemini models this key can use and save the v4 choice to models_config.json.

main: "Gemini 3.8 Flash", else the closest (highest-version) Flash model.
lite: the best Flash Lite, preferring 3.5, then 3.1, then the highest version.
Stable IDs are preferred over preview / experimental / dated ones of the same version.
Free-tier limits are the ones given in the v4 brief.
Usage (conda env civion): python pick_models.py   (never prints the key)
"""
import json
import re

from gemini_call import CONFIG_FILE, make_client

LIMITS = {"main": {"rpm": 5, "tpm": 250_000, "rpd": 20},
          "lite": {"rpm": 15, "tpm": 250_000, "rpd": 500}}
SKIP = re.compile(r"image|tts|live|audio|embedding|computer|robotics", re.I)


def version(mid):
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", mid)
    return float(m.group(1)) if m else 0.0


def stable(mid):
    return 0 if re.search(r"preview|exp|\d{2}-\d{2}|latest", mid) else 1


def main():
    client = make_client()
    models = [m for m in client.models.list() if "generateContent" in (m.supported_actions or [])]
    flash = sorted((m.name.replace("models/", ""), m.display_name) for m in models
                   if "flash" in m.name.lower() and not SKIP.search(m.name))
    print("Flash-family text models available to this key:")
    for mid, disp in flash:
        print(f"  {mid:45s} {disp}")
    names = dict(flash)
    main_c = [m for m, _ in flash if "lite" not in m]
    lite_c = [m for m, _ in flash if "lite" in m]

    exact = [m for m in main_c if m.startswith("gemini-3.8-flash")]
    main_id = max(exact or main_c, key=lambda m: (version(m), stable(m)))
    main_note = "exact Gemini 3.8 Flash" if exact else "no 3.8 Flash available: highest-version Flash"
    lite_id, lite_note = None, None
    for v in ("3.5", "3.1"):
        c = [m for m in lite_c if m.startswith(f"gemini-{v}-")]
        if c:
            lite_id, lite_note = max(c, key=stable), f"Flash Lite {v}"
            break
    if lite_id is None:
        lite_id = max(lite_c, key=lambda m: (version(m), stable(m)))
        lite_note = "no 3.5/3.1 Flash Lite: highest-version Flash Lite"

    cfg = {"main": {"id": main_id, "display_name": names[main_id], "note": main_note, "limits": LIMITS["main"]},
           "lite": {"id": lite_id, "display_name": names[lite_id], "note": lite_note, "limits": LIMITS["lite"]},
           "available_flash_models": [m for m, _ in flash]}
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"\nmain: {main_id} ({main_note})\nlite: {lite_id} ({lite_note})\nsaved {CONFIG_FILE}")


if __name__ == "__main__":
    main()
