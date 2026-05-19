# Game Deal-Finding MAS with SPADE and BDI Reasoning

This project is a course prototype for a multi-agent system, also called an MAS. It is implemented with **SPADE**, uses **Prosody/XMPP** for agent communication, and manually adds **BDI-style reasoning** so the agents can show beliefs, goals, plans, selected plans, and reasoning traces.

The system demonstrates two working scenarios:

1. **Software deal search**  
   The system searches for a PC game deal, resolves ambiguous titles, queries multiple source agents, uses a live CheapShark source by default, converts CheapShark USD prices to EUR using the European Central Bank reference rate, compares legitimate EUR-comparable deals, and warns about gray-market options.

2. **Local console search**  
   The system searches for local PlayStation 5 offers, resolves ambiguous console editions, collects official and marketplace options, ranks them by price, shipping, trust, condition, and distance, and prints risk warnings.

The project is not a production shopping system. It does not buy products, handle payments, scrape websites, or guarantee real-world availability. It is built to demonstrate agent cooperation, BDI-style reasoning, decision making, and controlled integration with a live source.

## Current verified implementation state

The current verified test result is:

```text
112 passed
```

The current verified behavior is:

```text
Software scenario:
- ambiguous title input such as "crimson" asks for clarification
- exact title rerun uses match_mode=exact
- CheapShark is active by default
- CheapShark is queried only after internal title resolution
- CheapShark deals are fetched by exact CheapShark gameID
- related products such as Deluxe Pack are rejected for the base game
- ECB currency conversion is active by default
- converted CheapShark deals can compete in EUR ranking
- gray-market offers are shown only as warnings

Local console scenario:
- ambiguous input such as "Playstation" asks for clarification
- exact edition rerun works
- official and marketplace sources are queried
- local deals are ranked by value
- used, refurbished, and lower-trust offers are warned about
```

## Assignment fit

The third project requirements ask for:

- at least two scenarios from the MAS design
- emphasis on goals, cooperation, and decision making
- at least one scenario with non-trivial decision making
- BDI-style reasoning
- a clear demonstration of beliefs, goals, and plans
- a report with agent descriptions and screenshots
- all project files and the report in one ZIP file

This implementation satisfies those requirements as follows:

| Requirement | How this project satisfies it |
|---|---|
| At least two scenarios | Software deal search and local console search |
| Agent cooperation | Coordinator, source, decision, and output agents communicate over SPADE/XMPP |
| Non-trivial decision making | Ambiguity resolution, source selection, mock fallback, currency conversion, gray-market avoidance, local ranking |
| BDI-style reasoning | Manual BDI layer in `app/bdi.py` and BDI-enabled agents |
| Beliefs, goals, plans | Stored in `BDIState`, written to `bdi_trace.json`, and explained in `BDI_DESIGN.md` |
| Screenshots | Runtime logs from both scenarios should be captured for the report |
| Submit as ZIP | Package the clean source code and report as `group_name_third_project.zip` |

## Main technologies

| Technology | Purpose |
|---|---|
| Python 3.12.x | Required runtime |
| SPADE | Multi-agent framework |
| Prosody | XMPP server used by SPADE agents |
| Docker Compose | Runs Prosody and optionally the app service |
| CheapShark API | Live online PC game deal source |
| European Central Bank reference rates | Live USD to EUR exchange-rate source |
| pytest | Automated test suite |

## Python version requirement

This project is designed for **Python 3.12.x only**.

The project enforces this requirement through:

- `.python-version`
- `pyproject.toml`
- `Dockerfile`
- `app/python_guard.py`
- test guard in `tests/conftest.py`

Do not run the project with Python 3.13 or newer.

## Project folder overview

```text
gamers_mas/
|- app/
|  |- agents/                 # SPADE agents
|  |- currency/               # ECB rate source and USD to EUR conversion
|  |- sources/                # mock and CheapShark deal source adapters
|  |- bdi.py                  # lightweight BDI structures
|  |- bdi_trace_store.py      # persistent BDI trace writer
|  |- matching.py             # normalization, fuzzy matching, exact matching
|  |- mock_data.py            # deterministic mock data
|  |- protocols.py            # message protocol names
|  |- request_bus.py          # request handoff file helpers
|  |- request_loader.py       # request validation and loading
|  |- runtime_response.py     # response handoff file helpers
|  `- settings.py             # environment variable configuration
|- infra/prosody/
|  `- prosody.cfg.lua         # Prosody configuration
|- scripts/
|  |- bootstrap_prosody_accounts.sh
|  |- create_venv_windows.ps1
|  |- create_venv_unix.sh
|  `- live_cheapshark_smoke_test.py
|- tests/                     # automated tests
|- main.py                    # starts the long-running MAS service
|- launcher.py                # submits requests to the running MAS
|- docker-compose.yml
|- Dockerfile
|- requirements.txt
|- pyproject.toml
|- README.md
|- ARCHITECTURE.md
|- BDI_DESIGN.md
|- SOURCE_INTEGRATION.md
|- TESTING.md
|- SETUP_GUIDE.md
|- TROUBLESHOOTING.md
|- SCREENSHOT_GUIDE.md
`- SUBMISSION_CHECKLIST.md
```

## Important runtime files

The project creates temporary runtime files while it is running.

| File | Purpose | Commit to Git? |
|---|---|---|
| `request.json` | Launcher writes a request for the MAS | No |
| `runtime_response.json` | Output agent writes the response for the launcher | No |
| `bdi_trace.json` | Persistent BDI audit trace | Usually no, unless copied to examples |
| `.env` | Local passwords and runtime settings | No |
| `.env.example` | Safe template configuration | Yes |

## Configuration defaults

The default `.env.example` enables live CheapShark and live ECB conversion:

```text
USE_REAL_CHEAPSHARK=true
CHEAPSHARK_TIMEOUT_SECONDS=8

ENABLE_CURRENCY_CONVERSION=true
CURRENCY_RATE_PROVIDER=ecb
CURRENCY_RATE_TIMEOUT_SECONDS=8
ALLOW_CURRENCY_FALLBACK_RATE=true
FALLBACK_USD_TO_EUR_RATE=0.92
FALLBACK_USD_TO_EUR_RATE_SOURCE=manual_fallback_rate
FALLBACK_USD_TO_EUR_RATE_DATE=2026-05-08
```

Meaning:

- CheapShark is used first for authorized reseller software deals.
- If CheapShark fails, returns no usable deals, or cannot be reached, the authorized reseller agent falls back to mock data.
- ECB is used first for USD to EUR conversion.
- If ECB fails and fallback is allowed, the configured fallback rate from `.env` is used.
- The output explains the original USD price, converted EUR price, conversion rate, rate source, and rate date.

## Supported title behavior

The software scenario does not accept arbitrary game titles yet.

Current controlled software catalog examples:

```text
Crimson Desert
Crimson Desert Deluxe Edition
```

Input such as:

```text
crimson
```

is intentionally ambiguous and asks the user to choose one exact title.

The local console scenario currently supports:

```text
PlayStation 5 Disc Edition
PlayStation 5 Digital Edition
```

Input such as:

```text
Playstation
```

is intentionally ambiguous and asks the user to choose one exact edition.

This controlled catalog is intentional. It prevents the system from mixing base games, deluxe editions, packs, DLCs, or console variants.

## Quick start on Windows

Open PowerShell in the project root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

Open a second PowerShell terminal in the same project root:

```powershell
.\.venv\Scripts\Activate.ps1
python launcher.py
```

## Quick start on Linux

Open a terminal in the project root.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

Open a second terminal in the same project root:

```bash
source .venv/bin/activate
python launcher.py
```

## Quick start on macOS

Install Python 3.12 first. One common option is Homebrew:

```bash
brew install python@3.12
```

Then open a terminal in the project root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
docker compose up -d prosody
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
pytest -q
python main.py
```

Open a second terminal in the same project root:

```bash
source .venv/bin/activate
python launcher.py
```

## Running the software scenario

Start the MAS service first:

```bash
python main.py
```

In another terminal:

```bash
python launcher.py
```

Choose:

```text
1
```

For ambiguity testing, enter:

```text
crimson
```

Expected behavior:

```text
Matching issue: your input is ambiguous.
Please choose one of these:
- Crimson Desert
- Crimson Desert Deluxe Edition
```

Then choose `Crimson Desert`.

Expected final behavior:

- CheapShark is queried.
- ECB conversion is applied.
- The recommended legitimate deal may come from CheapShark if its converted EUR price is best.
- Gray-market offers are shown only as warnings.

## Running the local console scenario

Start the MAS service first:

```bash
python main.py
```

In another terminal:

```bash
python launcher.py
```

Choose:

```text
2
```

Use:

```text
Playstation
500
15
```

Expected behavior:

```text
Matching issue: your input is ambiguous.
Please choose one of these:
- PlayStation 5 Digital Edition
- PlayStation 5 Disc Edition
```

After selecting an edition, the system ranks official and marketplace offers and prints warnings for used, refurbished, and lower-trust results.

## Docker usage

The usual development flow is:

1. Run Prosody through Docker.
2. Run `main.py` and `launcher.py` locally inside the Python virtual environment.

Start Prosody:

```bash
docker compose up -d prosody
```

Register the accounts:

```bash
docker compose exec prosody sh /scripts/bootstrap_prosody_accounts.sh
```

Stop Prosody:

```bash
docker compose down
```

You can also start both Prosody and the app container:

```bash
docker compose up --build
```

For interactive launcher work, the local two-terminal approach is easier.

## Recommended reading order

For a new user, read the documents in this order:

1. `README.md` - overview and quick start
2. `SETUP_GUIDE.md` - detailed setup for Windows, Linux, and macOS
3. `ARCHITECTURE.md` - how the MAS is built
4. `BDI_DESIGN.md` - how beliefs, goals, and plans are represented
5. `SOURCE_INTEGRATION.md` - CheapShark, ECB, and fallback logic
6. `TESTING.md` - how to verify the project
7. `TROUBLESHOOTING.md` - common errors and fixes

## References used by the implementation

- SPADE: https://spade-mas.readthedocs.io/
- Prosody: https://prosody.im/
- CheapShark API: https://apidocs.cheapshark.com/
- ECB euro foreign exchange reference rates: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- ECB reference rates information page: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
