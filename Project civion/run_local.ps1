# Run CIVION locally (backend :8000 + frontend :5173) in two windows. Use the conda env "civion".
#   powershell -ExecutionPolicy Bypass -File run_local.ps1
# Keys come from Project civion\.env (GEMINI_API_KEY for extraction, GROQ_API_KEY for the chat).
# CIVION_MD_SOURCE: prebuilt (default, demo: Docling skipped, reads demo_md\<pdf name>.md) | docling
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $env:USERPROFILE "miniconda3\envs\civion\python.exe"

Start-Process powershell -WorkingDirectory $root -ArgumentList "-NoExit", "-Command", "& '$py' -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -WorkingDirectory (Join-Path $root "frontend") -ArgumentList "-NoExit", "-Command", "npm run dev"
Write-Host "Backend  http://127.0.0.1:8000"
Write-Host "Frontend http://localhost:5173  (open this one)"
