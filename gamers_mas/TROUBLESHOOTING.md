# Troubleshooting Guide

This guide explains common problems and how to fix them.

## Problem: Python version error

### Symptom

```text
This project requires Python 3.12.x
```

### Cause

You are using Python 3.13, 3.14, or another unsupported version.

### Fix on Windows

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Fix on Linux/macOS

```bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
```

## Problem: PowerShell cannot activate virtual environment

### Symptom

```text
running scripts is disabled on this system
```

### Fix

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Problem: missing environment variable

### Symptom

```text
Missing required environment variable
```

### Cause

`.env` does not exist or is missing values.

### Fix

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

## Problem: cannot connect to XMPP server

### Symptom

Agents start slowly, fail to connect, or messages do not move.

### Cause

Prosody is not running, or the XMPP domain is wrong.

### Fix

Start Prosody:

```bash
docker compose up -d prosody
```

Check containers:

```bash
docker compose ps
```

For local Python runs, `.env` should normally contain:

```text
XMPP_DOMAIN=localhost
```

For full Docker app service mode, use the Compose service networking carefully. The default package is optimized for local Python plus Docker Prosody.

## Problem: agent accounts are missing

### Symptom

SPADE cannot authenticate agents.

### Fix

```bash
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

If the accounts already exist, the command may print messages about existing users. That is acceptable.

## Problem: bootstrap script path not found

### Symptom

```text
No such file or directory: /scripts/bootstrap_prosody_accounts.sh
```

### Cause

The Compose volume or container is not from the current project version.

### Fix

Check `docker-compose.yml` contains:

```text
./scripts/bootstrap_prosody_accounts.sh:/scripts/bootstrap_prosody_accounts.sh:ro
```

Then restart:

```bash
docker compose down
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

## Problem: launcher waits or returns no response

### Possible causes

- `main.py` is not running.
- Prosody is not running.
- agent accounts are not registered.
- old `request.json` or `runtime_response.json` files are interfering.

### Fix

Stop `main.py`, then clean runtime files.

Windows:

```powershell
Remove-Item request.json,runtime_response.json -ErrorAction SilentlyContinue
```

Linux/macOS:

```bash
rm -f request.json runtime_response.json
```

Then restart:

```bash
python main.py
```

and run launcher again.

## Problem: `runtime_response.json` disappears

This can be normal.

`runtime_response.json` is temporary. `launcher.py` may read it and clear it. Use `bdi_trace.json` for persistent reasoning evidence.

## Problem: `bdi_trace.json` is missing

### Cause

No request has completed yet, or the file was cleaned.

### Fix

Run a scenario through `launcher.py`. After completion:

Windows:

```powershell
Get-Content bdi_trace.json
```

Linux/macOS:

```bash
cat bdi_trace.json
```

## Problem: CheapShark is unavailable

### Symptom

The authorized reseller agent prints a real source error or falls back to mock data.

### Expected behavior

This is acceptable. The BDI plan should become:

```text
fallback_to_mock_source
```

The MAS should continue.

### Things to check

- internet connection
- `USE_REAL_CHEAPSHARK=true`
- `CHEAPSHARK_TIMEOUT_SECONDS=8`

## Problem: ECB exchange rate source is unavailable

### Expected behavior

If fallback is enabled:

```text
ALLOW_CURRENCY_FALLBACK_RATE=true
```

the system should use:

```text
FALLBACK_USD_TO_EUR_RATE
FALLBACK_USD_TO_EUR_RATE_SOURCE
FALLBACK_USD_TO_EUR_RATE_DATE
```

The output should still mention the fallback source.

## Problem: CheapShark returns a related product

### Expected behavior after current fix

The adapter should reject related products unless the returned CheapShark title exactly matches the resolved title.

Example:

```text
Resolved title: Crimson Desert
Reject: Crimson Desert Deluxe Pack
Reject: Crimson Desert Digital Deluxe
Accept: Crimson Desert
```

If related products still get recommended, inspect `app/sources/cheapshark_source.py` and the tests:

```text
tests/test_cheapshark_title_filtering.py
```

## Problem: arbitrary game title does not work

This is expected.

The project uses an internal catalog before querying CheapShark. Unknown titles are not passed directly to CheapShark.

Supported examples:

```text
Crimson Desert
Crimson Desert Deluxe Edition
```

Unsupported arbitrary examples may return not found.

This keeps the demo safe from edition and DLC mixing.

## Problem: local console scenario does not use CheapShark

This is expected.

CheapShark is for online PC game deals. Local console deals use mock official and marketplace data.

## Problem: tests fail after changing `.env`

Most tests should not depend on live services, but settings parsing tests may be affected by invalid values.

Check:

```text
USE_REAL_CHEAPSHARK=true
ENABLE_CURRENCY_CONVERSION=true
CURRENCY_RATE_PROVIDER=ecb
FALLBACK_USD_TO_EUR_RATE=0.92
```

Run:

```bash
pytest -q
```

## Problem: Docker container keeps old state

Restart Compose:

```bash
docker compose down
docker compose up -d prosody
```

If needed, rebuild the app container:

```bash
docker compose build --no-cache app
```

## Problem: `.env` appears in Git status

`.env` should not be committed.

Check `.gitignore` contains:

```text
.env
.env.*
!.env.example
```

If `.env` was already tracked, remove it from Git tracking without deleting local file:

```bash
git rm --cached .env
```

## Problem: `__pycache__` appears in ZIP

Clean before packaging.

Windows:

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Include *.pyc -File | Remove-Item -Force
```

Linux/macOS:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Problem: package ZIP includes runtime artifacts

Do not include:

```text
.env
.venv/
__pycache__/
.pytest_cache/
bdi_trace.json
request.json
runtime_response.json
```

Keep:

```text
.env.example
```

## Last-resort reset

If the project is in a confused runtime state:

1. Stop `main.py`.
2. Stop Docker Compose.
3. Clean runtime files.
4. Start Prosody.
5. Bootstrap accounts.
6. Run tests.
7. Start `main.py`.
8. Run `launcher.py`.

Commands:

```bash
docker compose down
rm -f request.json runtime_response.json bdi_trace.json
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```
