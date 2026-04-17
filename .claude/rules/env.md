# Environment Rules

## Virtual Environment — Required

Always work inside a Python virtual environment. Never install packages into the system Python.

### Create & Activate

```bash
# Create (run once, from repo root)
python -m venv .venv

# Activate — Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate — Windows (CMD)
.venv\Scripts\activate.bat

# Activate — macOS / Linux
source .venv/bin/activate
```

The `.venv/` directory is already in `.gitignore` — do not commit it.

### Install Dependencies

```bash
# After activating the venv
pip install -r backend/requirements.txt

# If frontend dependencies are needed
cd frontend && npm install
```

### Verify Correct Environment

```bash
# Should point inside .venv, not system Python
which python      # macOS/Linux
where python      # Windows
```

## Environment Variables

Never hardcode secrets or API keys in source code.

1. Copy the template:
   ```bash
   cp .env.example .env
   ```
2. Fill in all values in `.env` before running anything.
3. `.env` is gitignored — never commit it.

### Loading `.env`

The backend loads `.env` automatically via `python-dotenv`. Add to `backend/requirements.txt` if not present:
```
python-dotenv
```

In `backend/main.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Required `.env` Keys

```bash
# LLM
GOOGLE_API_KEY=

# OSINT
TAVILY_API_KEY=
PROXYCURL_API_KEY=
GITHUB_PAT=

# Email
GMAIL_OAUTH_CLIENT_ID=
GMAIL_OAUTH_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=

# GCP
GCP_PROJECT_ID=
GCP_REGION=
VERTEX_AI_INDEX_ID=

# Database
DATABASE_URL=

# Firebase
FIREBASE_SERVICE_ACCOUNT_JSON=
```

## Docker (Alternative to Local Venv)

If using Docker instead of a local venv:

```bash
# Start all services
docker-compose up

# Start and rebuild images
docker-compose up --build

# Backend only
docker-compose up backend
```

Docker containers manage their own isolated Python environment — no local venv needed when using Docker.

## Dependency Management

- All Python packages go in `backend/requirements.txt` with **pinned versions**.
- After installing a new package: `pip freeze > backend/requirements.txt`
- Do not use `pip install` without immediately updating `requirements.txt`.

## Python Version

Use **Python 3.11+**. The project uses `asyncio`, type hints, and `TypedDict` features that require 3.11 or later.

```bash
python --version   # Must be 3.11.x or higher
```
