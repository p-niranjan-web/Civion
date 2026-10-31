"""Lists Gemini models for your key, picks main (3.8 Flash) + Flash Lite IDs, saves to models_config.json.
Run (conda env civion):  python pick_models.py
Never prints the key."""
import os, re, json, getpass, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ENV = next((p / ".env" for p in [HERE, *HERE.parents] if (p / ".env").exists()), HERE / ".env")

def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))

load_env()
if not os.environ.get("GEMINI_API_KEY"):
    key = getpass.getpass("Paste GEMINI_API_KEY (hidden): ").strip()
    with open(ENV, "a", encoding="utf-8") as f:
        f.write(("\n" if ENV.exists() and not ENV.read_text().endswith("\n") else "") + f"GEMINI_API_KEY={key}\n")
    os.environ["GEMINI_API_KEY"] = key
    print(f"Saved GEMINI_API_KEY to {ENV}")

# .env must be gitignored
ign = [p / ".gitignore" for p in [HERE, *HERE.parents] if (p / ".gitignore").exists()]
if not any(".env" in g.read_text(errors="ignore") for g in ign):
    print("WARNING: .env is not in any .gitignore - add it before committing.")

from google import genai
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
models = [m for m in client.models.list() if "generateContent" in (m.supported_actions or [])]
flash = sorted(((m.name.replace("models/", ""), m.display_name) for m in models if "flash" in m.name.lower()))
print("\nFlash-family models available:")
for i, d in flash:
    print(f"  {i}  |  {d}")

def ver(i):
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", i)
    return float(m.group(1)) if m else 0.0
def stable_first(i):  # prefer non-preview/exp/dated
    return 0 if re.search(r"preview|exp|\d{2}-\d{2}|latest", i) else 1

main_c = [i for i, _ in flash if "lite" not in i and not re.search(r"image|tts|live|audio|thinking-exp", i)]
lite_c = [i for i, _ in flash if "lite" in i and not re.search(r"image|tts|live|audio", i)]

exact = [i for i in main_c if i.startswith("gemini-3.8-flash")]
main = max(exact, key=stable_first) if exact else max(main_c, key=lambda i: (ver(i), stable_first(i)), default=None)
main_note = "exact 3.8 Flash match" if exact else "NO exact 3.8 match - closest (highest-version) Flash"

lite = None
for v in ("3.5", "3.1"):
    c = [i for i in lite_c if f"gemini-{v}-" in i]
    if c:
        lite = max(c, key=stable_first); break
if not lite and lite_c:
    lite = max(lite_c, key=lambda i: (ver(i), stable_first(i)))

cfg = {"main_model": main, "lite_model": lite}
(HERE / "models_config.json").write_text(json.dumps(cfg, indent=2))
print(f"\nMAIN : {main}  ({main_note})\nLITE : {lite}\nSaved -> {HERE / 'models_config.json'}")
