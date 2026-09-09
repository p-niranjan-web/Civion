# CIVION AI

Structural compliance engine for IS 456:2000 concrete specifications. Upload a
specification PDF, and CIVION parses it, runs a compliance audit, and lets you
chat about the results and generate a rectified specification.

> **Repository layout:** all application code lives in the **`Project civion/`**
> folder. Every command below assumes you have `cd`'d into it first.

The app is **two processes that run at the same time**:

| Process  | Folder                     | Tech            | Local URL               |
|----------|----------------------------|-----------------|-------------------------|
| Backend  | `Project civion/api/`      | FastAPI + Groq  | http://127.0.0.1:8000   |
| Frontend | `Project civion/frontend/` | React + Vite    | http://localhost:5173   |

The frontend calls the backend at `http://127.0.0.1:8000` when it runs on
localhost, so **both must be running** — otherwise every request shows
"Failed to fetch".

---

## Prerequisites

- **Python 3.11+** (3.13 works). Conda or plain `python`/`pip` are both fine.
- **Node.js 18+** and npm.
- A **Groq API key** (`GROQ_API_KEY`). Get one at https://console.groq.com.

---

## 1. Backend setup

Open a terminal and move into the app folder:

```powershell
cd "Project civion"
```

### Install dependencies

Using conda (recommended — keeps things isolated):

```powershell
conda create -n civion python=3.11 -y
conda activate civion
pip install -r requirements.txt
```

Or without a virtual environment (simpler, installs into your current env):

```powershell
pip install -r requirements.txt
```

### Run the backend

**Option A: Using a `.env` file (Recommended for convenience)**

Create a file named `.env` in `Project civion/`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Then start the backend:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

**Option B: Setting the environment variable in terminal**

**PowerShell (Windows):**

```powershell
$env:GROQ_API_KEY = "your_groq_api_key_here"
python -m uvicorn api.main:app --reload --port 8000
```

**bash / macOS / Linux:**

```bash
export GROQ_API_KEY="your_groq_api_key_here"
uvicorn api.main:app --reload --port 8000
```

Wait for:

```
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open. Verify by opening http://127.0.0.1:8000 in a browser —
you should see `{"message":"Civion AI Backend is Running Successfully!"}`.

> **Note:** If you use a `.env` file in `Project civion/`, uvicorn will automatically load the `GROQ_API_KEY` every time you run it.

---

## 2. Frontend setup

Open a **second** terminal:

```powershell
cd "Project civion/frontend"
npm install
npm run dev
```

Open the URL it prints (usually http://localhost:5173).

---

## 3. Using the app

1. In the sidebar, drag in a specification **PDF** (or click to browse).
2. Set the **Environmental Exposure** condition:
   - **I know it** — pick one of Mild / Moderate / Severe / Very Severe / Extreme, or
   - **Help me decide** — answer the short questionnaire and CIVION derives the class.
3. Click **Run Compliance Audit**.
4. Review the Dashboard, Compliance Ledger, and Engineering Traceability tabs.
5. To try a different exposure class, change it in the sidebar and click
   **Re-run Compliance Audit** — the document is re-parsed for the new exposure case.
6. Use **Make Specs Better** to generate an optimized/rectified specification and PDF.

---

## Project layout

```
Project civion/
├── api/main.py         FastAPI app — /api/audit, /api/chat, /api/optimize, /api/report/*
├── parser.py           PDF text extraction + multi-agent JSON extraction (Groq)
├── auditor.py          IS 456 compliance checks over the extracted JSON
├── database.py         IS 456 rule tables (durability, cover, sulphate, sampling, …)
├── config.py           Groq client / GROQ_API_KEY handling
├── requirements.txt    Backend Python dependencies
├── downloads/          Generated PDFs + parser cache (downloads/cache/)
└── frontend/           React + Vite single-page app
    └── src/
        ├── App.jsx
        └── components/  Sidebar, Dashboard, Ledger, Traceability, Optimization,
                         ExposureSelector, ChatWindow, RadialGauge, ScannerAnimation
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Failed to fetch" in the UI | Backend not running on port 8000 | Start the backend (step 1) |
| `No module named uvicorn` | Python deps not installed | `pip install -r requirements.txt` |
| 500 error mentioning `GROQ_API_KEY` | Key not set in the backend's terminal | `set`/`export` the key, restart uvicorn |
| `Could not import module "api.main"` | Ran uvicorn from the wrong folder | Run it from `Project civion/`, not from `api/` |
| Port 8000 already in use | An old backend is still running | Kill it, or use `--port 8001` (and update `API_BASE` in `frontend/src/App.jsx`) |
| Parser returns the same result after changing inputs | Deterministic cache in `downloads/cache/` | Delete the relevant `.json` there (or the whole folder) |

---

## Deployment (Vercel)

`vercel.json` builds the frontend (`frontend/dist`) and routes `/api/*` to
`api/main.py` as a serverless function. Set `GROQ_API_KEY` as a project
environment variable in the Vercel dashboard. In production the frontend uses a
same-origin (empty) API base, so no separate backend URL is needed.
