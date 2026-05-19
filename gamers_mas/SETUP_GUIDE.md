# Setup Guide

This guide explains how to set up and run the project on Windows, Linux, and macOS.

## Before you start

You need:

- Python 3.12.x
- Git, if you are cloning from a repository
- Docker Desktop or Docker Engine
- internet access for CheapShark and ECB live source runtime tests
- PowerShell on Windows
- Bash or Zsh on Linux/macOS

## Important rule: Python 3.12 only

The project intentionally blocks Python versions outside 3.12.x.

Check your Python version:

```bash
python --version
```

or:

```bash
python3.12 --version
```

Expected:

```text
Python 3.12.x
```

## Windows setup

### Step 1: install Python 3.12

Option A: install from python.org.

Option B: use winget:

```powershell
winget install Python.Python.3.12
```

Then check:

```powershell
py -3.12 --version
```

### Step 2: open PowerShell in the project root

The project root is the folder that contains:

```text
main.py
launcher.py
requirements.txt
docker-compose.yml
```

### Step 3: create the virtual environment

```powershell
py -3.12 -m venv .venv
```

### Step 4: activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again.

### Step 5: install dependencies

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 6: create the environment file

```powershell
Copy-Item .env.example .env
```

### Step 7: start Prosody

```powershell
docker compose up -d prosody
```

### Step 8: register agent accounts

```powershell
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

If it says accounts already exist, that is acceptable.

### Step 9: run tests

```powershell
pytest -q
```

Expected:

```text
112 passed
```

### Step 10: start the MAS

Terminal A:

```powershell
python main.py
```

### Step 11: run the launcher

Terminal B:

```powershell
.\.venv\Scripts\Activate.ps1
python launcher.py
```

## Linux setup

### Step 1: install Python 3.12

Package names differ by distribution.

On Ubuntu, Python 3.12 may already be available on newer releases. Check:

```bash
python3.12 --version
```

If needed, install with your distribution package manager or use pyenv.

### Step 2: open a terminal in the project root

The project root contains:

```text
main.py
launcher.py
requirements.txt
docker-compose.yml
```

### Step 3: create the virtual environment

```bash
python3.12 -m venv .venv
```

### Step 4: activate it

```bash
source .venv/bin/activate
```

### Step 5: install dependencies

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 6: create the environment file

```bash
cp .env.example .env
```

### Step 7: start Prosody

```bash
docker compose up -d prosody
```

### Step 8: register accounts

```bash
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

### Step 9: run tests

```bash
pytest -q
```

Expected:

```text
112 passed
```

### Step 10: start the MAS

Terminal A:

```bash
python main.py
```

### Step 11: run the launcher

Terminal B:

```bash
source .venv/bin/activate
python launcher.py
```

## macOS setup

### Step 1: install Python 3.12

With Homebrew:

```bash
brew install python@3.12
```

Check:

```bash
python3.12 --version
```

### Step 2: open Terminal in the project root

The project root contains:

```text
main.py
launcher.py
requirements.txt
docker-compose.yml
```

### Step 3: create the virtual environment

```bash
python3.12 -m venv .venv
```

### Step 4: activate it

```bash
source .venv/bin/activate
```

### Step 5: install dependencies

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 6: create the environment file

```bash
cp .env.example .env
```

### Step 7: start Prosody

Make sure Docker Desktop is running.

```bash
docker compose up -d prosody
```

### Step 8: register accounts

```bash
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

### Step 9: run tests

```bash
pytest -q
```

Expected:

```text
112 passed
```

### Step 10: start the MAS

Terminal A:

```bash
python main.py
```

### Step 11: run the launcher

Terminal B:

```bash
source .venv/bin/activate
python launcher.py
```

## Docker-only app mode

The app service is defined in `docker-compose.yml`.

Build and run both Prosody and the app container:

```bash
docker compose up --build
```

This starts `main.py` inside the app container.

For interactive `launcher.py` use, the local virtual environment method is usually simpler.

## Common run sequence

Start Prosody:

```bash
docker compose up -d prosody
```

Start the MAS:

```bash
python main.py
```

Use the launcher in another terminal:

```bash
python launcher.py
```

Stop the MAS:

```text
Ctrl+C
```

Stop Prosody:

```bash
docker compose down
```

## Scenario inputs to try

### Software scenario

```text
1
crimson
```

Choose:

```text
Crimson Desert
```

Expected:

- ambiguity handling
- exact rerun
- CheapShark live source
- ECB conversion
- gray-market warning

### Local console scenario

```text
2
Playstation
500
15
```

Choose:

```text
PlayStation 5 Disc Edition
```

Expected:

- ambiguity handling
- exact rerun
- ranked local deals
- used/refurbished/trust warnings

## Environment settings

Default important settings:

```text
USE_REAL_CHEAPSHARK=true
ENABLE_CURRENCY_CONVERSION=true
CURRENCY_RATE_PROVIDER=ecb
ALLOW_CURRENCY_FALLBACK_RATE=true
```

Do not commit `.env`.

Commit `.env.example`.

## Cleaning runtime files

Windows:

```powershell
Remove-Item request.json,runtime_response.json,bdi_trace.json -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force
```

Linux/macOS:

```bash
rm -f request.json runtime_response.json bdi_trace.json
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
```

## Do not delete these

Keep:

```text
.env.example
.python-version
requirements.txt
pyproject.toml
docker-compose.yml
Dockerfile
scripts/
infra/
tests/
app/
```
