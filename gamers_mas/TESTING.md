# Testing

This document explains how to test the Game Deal-Finding MAS on Windows, Linux, and macOS.

The current verified result is:

```text
112 passed
```

## What the tests cover

The automated tests cover:

- Python 3.12 enforcement
- matching and ambiguity handling
- launcher ambiguity resolution
- BDI core structures
- BDI plan decisions
- BDI trace persistence
- software coordinator BDI behavior
- local coordinator BDI behavior
- authorized reseller BDI source selection
- recommendation BDI behavior
- value ranking BDI behavior
- mock source adapters
- CheapShark source adapter
- CheapShark exact gameID lookup
- strict title filtering against related products
- ECB XML parsing
- USD to EUR conversion
- currency fallback behavior
- output formatting for converted prices
- source-agent adapter behavior

## Test prerequisites

Before testing:

1. Use Python 3.12.x.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Copy `.env.example` to `.env`.
5. Docker is only required for runtime tests with Prosody, not for most unit tests.

## Run tests on Windows

Open PowerShell in the project root:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

Expected:

```text
112 passed
```

If the virtual environment does not exist yet:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
pytest -q
```

## Run tests on Linux

Open a terminal in the project root:

```bash
source .venv/bin/activate
pytest -q
```

If the virtual environment does not exist yet:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
pytest -q
```

## Run tests on macOS

Open Terminal or iTerm in the project root:

```bash
source .venv/bin/activate
pytest -q
```

If Python 3.12 is not installed, one option is:

```bash
brew install python@3.12
```

Then:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
pytest -q
```

## Test file guide

| Test file | What it checks |
|---|---|
| `test_matching_and_ambiguity.py` | normalization, fuzzy matching, exact matching, catalog ambiguity |
| `test_launcher_ambiguity_resolution.py` | launcher rewrites ambiguous fuzzy request to exact rerun |
| `test_bdi_core.py` | BDIState, Goal, Plan, PlanDecision |
| `test_bdi_trace_store.py` | trace file creation, append behavior, invalid JSON handling |
| `test_software_coordinator_agent_bdi.py` | software title BDI plans |
| `test_local_coordinator_agent_bdi.py` | local console product BDI plans |
| `test_authorized_reseller_source_bdi.py` | authorized reseller source-selection BDI |
| `test_authorized_reseller_live_source_wiring.py` | real source success, failure, empty result, mock fallback |
| `test_authorized_reseller_trace_forwarding.py` | AuthorizedResellerAgent trace reaches `bdi_trace.json` |
| `test_recommendation_agent_bdi.py` | recommendation plan selection |
| `test_recommendation_currency_safety.py` | USD deals are not compared before conversion |
| `test_value_ranker_agent_bdi.py` | local console value ranking |
| `test_mock_sources.py` | mock source adapters |
| `test_source_agent_adapters.py` | source agents use adapters |
| `test_source_settings.py` | environment variable parsing |
| `test_cheapshark_source.py` | CheapShark API mapping and exact gameID logic using fake responses |
| `test_cheapshark_title_filtering.py` | rejection of related CheapShark titles |
| `test_cheapshark_currency_conversion.py` | currency conversion of CheapShark deals |
| `test_ecb_rate_source.py` | ECB XML parsing |
| `test_currency_converter.py` | USD to EUR conversion and fallback |
| `test_foreign_currency_output.py` | output logic for foreign-currency deals |
| `test_output_converted_currency.py` | output logic for converted CheapShark deals |

## Runtime verification tests

Automated tests are necessary, but the report should also include screenshots of the agents running.

### Runtime test setup

Terminal A:

```bash
python main.py
```

Terminal B:

```bash
python launcher.py
```

Make sure Prosody is running before runtime tests:

```bash
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

If accounts already exist, the bootstrap command may report that. That is acceptable.

## Runtime test 1: software ambiguity and live source

In `launcher.py`, choose:

```text
1
crimson
```

Expected first part:

```text
Matching issue: your input is ambiguous.
Please choose one of these:
- Crimson Desert
- Crimson Desert Deluxe Edition
```

Choose:

```text
Crimson Desert
```

Expected second part:

```text
AuthorizedResellerAgent BDI selected plan: query_real_source
Returned authorized reseller deals using cheapshark
Recommended legitimate deal: ...
converted from ... USD
rate source=European Central Bank euro foreign exchange reference rates
WARNING: Gray-market option detected
```

This proves:

- ambiguity handling works
- exact rerun works
- CheapShark is active
- ECB conversion is active
- gray-market risk is handled
- BDI decisions are selected and printed

## Runtime test 2: local console ambiguity and ranking

In `launcher.py`, choose:

```text
2
Playstation
500
15
```

Expected first part:

```text
Matching issue: your input is ambiguous.
Please choose one of these:
- PlayStation 5 Digital Edition
- PlayStation 5 Disc Edition
```

Choose one edition.

Expected second part:

```text
Best overall deal: ...
Best official deal: ...
Best local pickup deal: ...
Top 3 ranked deals:
Warnings:
```

This proves:

- local ambiguity handling works
- exact rerun works
- ranking works
- warnings work

## Check BDI trace

After runtime runs:

```bash
cat bdi_trace.json
```

Windows PowerShell:

```powershell
Get-Content bdi_trace.json
```

For a software run, the latest entry should include:

```text
SoftwareCoordinatorAgent
AuthorizedResellerAgent
RecommendationAgent
```

For a local console run, the latest entry should include:

```text
LocalCoordinatorAgent
ValueRankerAgent
```

## Manual CheapShark smoke test

The project includes:

```text
scripts/live_cheapshark_smoke_test.py
```

Run:

```bash
python scripts/live_cheapshark_smoke_test.py "Crimson Desert"
```

Expected behavior:

- the script contacts CheapShark
- prints mapped deals
- shows USD source prices
- confirms currency-safety behavior

This script is manual and should not be part of normal `pytest`, because live external APIs can fail.

## When live APIs are unavailable

If CheapShark is unavailable:

- the authorized reseller agent falls back to mock data
- tests should still pass
- the MAS should not crash

If ECB is unavailable:

- conversion uses the configured fallback rate if `ALLOW_CURRENCY_FALLBACK_RATE=true`
- the output should still show the rate source as the fallback source

## What not to test as normal behavior

Do not expect arbitrary game titles to work.

Examples that are intentionally supported:

```text
Crimson Desert
Crimson Desert Deluxe Edition
```

Examples that may be rejected:

```text
Batman
Elden Ring
Cyberpunk
```

The system can query CheapShark only after internal catalog title resolution. This is a design choice to keep title safety and avoid mixing related games, packs, and editions.

## Useful pytest commands

Run all tests:

```bash
pytest -q
```

Run one file:

```bash
pytest -q tests/test_cheapshark_source.py
```

Run one test by name:

```bash
pytest -q -k exact_game
```

Show full output:

```bash
pytest -vv
```

Stop after first failure:

```bash
pytest -q -x
```

## Final verification checklist

Before packaging:

```bash
pytest -q
```

Expected:

```text
112 passed
```

Then verify both scenarios manually:

```text
Software scenario:
1
crimson
choose Crimson Desert

Local console scenario:
2
Playstation
500
15
choose PlayStation 5 Disc Edition
```

If these pass, the implementation is ready for documentation screenshots and packaging.
