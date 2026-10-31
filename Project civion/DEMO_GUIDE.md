# Running CIVION locally (demo)

## Start
```
powershell -ExecutionPolicy Bypass -File run_local.ps1
```
Opens the backend (http://127.0.0.1:8000) and the frontend (http://localhost:5173) in two windows. Use the conda env `civion`.
Keys are read from `Project civion\.env`: `GEMINI_API_KEY` (extraction) and `GROQ_API_KEY` (chat only).

## What happens on upload
```
PDF -> Markdown -> clean -> ONE Gemini call (gemini-3.8-flash) -> audit engine -> dashboard
```
- **Demo mode (default, `CIVION_MD_SOURCE=prebuilt`)**: the Docling step is skipped. The backend looks for
  `demo_md\<uploaded file name>.md`. Upload `with_Error_final_BLR_Airport_Cast-in-Concrete_with_mistakes.pdf`
  (or `BLR Airport (Cast-in-Concrete).pdf`); any other file name gives a clear error instead of a wrong result.
- **Normal mode (`CIVION_MD_SOURCE=docling` in `.env`)**: the uploaded PDF is converted with Docling
  (about 9 minutes for BLR; needs `pip install docling` in the env).
- The grading tables are read by Gemini itself (no Python table reader).

## For the video
- The first run takes **4-7 minutes** with `gemini-3.8-flash` (it thinks; 503 "high demand" retries add time).
  Cut the wait when editing, or switch to `GEMINI_MODEL=gemini-3.5-flash-lite` in `.env` (10-25 s, weaker quotes).
- Free tier: **20 calls/day** for 3.8-flash.
- Results are cached (`downloads/cache`, per document + exposure + concrete type + model): re-running the same
  combination is instant. Delete the cache file, or change the exposure, to force a fresh Gemini call.
- Pick the concrete type in the sidebar. "Auto-detect" assumes Reinforced Concrete (the v4 prompt was only tested with one given).
- Don't use `--reload` while recording; a file change would restart the server in the middle of a long call.

## Settings (`.env`)
| Key | Default | |
|---|---|---|
| `GEMINI_API_KEY` | - | required |
| `GEMINI_MODEL` | `gemini-3.8-flash` | `gemini-3.5-flash-lite` for speed |
| `CIVION_MD_SOURCE` | `prebuilt` | `docling` for real uploads |
| `GROQ_API_KEY` | - | chat endpoint only |
