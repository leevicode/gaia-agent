# Game Deal-Finding MAS with SPADE

This repository contains a **mock-data-only** prototype built to **demonstrate the workings of a multi-agent system (MAS) using SPADE**. It is not a production e-commerce system and it does not connect to live stores or real APIs.

## Python version constraint

This project is constrained to **Python 3.12.x only**.

The support package enforces that constraint in four ways:

- `Dockerfile` uses `python:3.12-slim`
- `pyproject.toml` declares `requires-python = ">=3.12,<3.13"`
- `.python-version` is set to `3.12`
- `main.py`, `launcher.py`, and the test suite fail fast if the interpreter is not Python 3.12.x

Do not use Python 3.13 or 3.14 for this project.

## What this version is for

This version is meant to show:

- how SPADE agents cooperate
- how requests are routed through coordinators
- how fuzzy matching and ambiguity detection work
- how a user resolves ambiguity and then reruns in exact mode
- how a MAS can return to an idle state between runs

## What this version is not

This version does **not**:

- scrape real websites
- call real commercial APIs
- persist data in a database
- handle payments or purchasing
- run as a production-grade service

## Runtime model

The current runtime model is a **long-running idle MAS service**:

1. Start the agents once with `main.py`
2. Leave them running in the background
3. Use `launcher.py` whenever you want to submit a new request
4. After each request finishes, the system returns to an idle state and waits for the next one
5. Stop the service manually when you are done

## Key files

- `main.py` - starts the full MAS service and keeps it idle between requests
- `launcher.py` - interactive console client that submits requests
- `request.json` - transient request handoff file
- `runtime_response.json` - transient response handoff file
- `app/mock_data.py` - mock catalogs for both scenarios
- `tests/` - automated test suite for matching and ambiguity logic
- `pyproject.toml` - Python version constraint metadata
- `.python-version` - local interpreter hint for Python version managers

## Installation

Install from:

```bash
pip install -r requirements.txt
```

`requirements.txt` is pinned to the current stable dependency set:

- `spade==4.1.2`
- `slixmpp-multiplatform==1.12.0`
- `python-dotenv==1.2.2`
- `pytest>=8,<9`

## Environment variables

Copy:

```text
.env.example -> .env
```

For local host execution, keep:

```text
XMPP_DOMAIN=localhost
```

For Docker full-stack execution, use:

```text
XMPP_DOMAIN=prosody
```

## Local setup on Windows

### Option A - explicit commands

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Option B - helper script

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create_venv_windows.ps1
```

Then:

```powershell
Copy-Item .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

In a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python launcher.py
```

## Local setup on Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

In a second terminal:

```bash
source .venv/bin/activate
python launcher.py
```

## Local setup on macOS

If `python3.12` is not available, install it first.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

In a second terminal:

```bash
source .venv/bin/activate
python launcher.py
```

## Full Docker stack

The full Docker stack also uses Python 3.12 because the `Dockerfile` is pinned to `python:3.12-slim`.

1. Set `XMPP_DOMAIN=prosody` in `.env`
2. Build and start the stack:

```bash
docker compose up --build -d prosody app
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

3. Watch logs:

```bash
docker compose logs -f app
```

4. Submit requests from inside the app container:

```bash
docker compose exec app python launcher.py
```

## Notes

- This package is designed to be stable first, then tested, then documented, then integrated with real sources later.
- If you see a Python version error, recreate the environment with Python 3.12.x instead of trying to continue with another interpreter.
