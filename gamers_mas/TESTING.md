# Testing

This project includes a small automated test suite focused on matching and ambiguity handling.

## Python constraint

Run the tests only under **Python 3.12.x**.

The test suite imports `tests/conftest.py`, which fails fast if the interpreter is not Python 3.12.x.

## Run tests

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

### Linux / macOS

```bash
source .venv/bin/activate
pytest -q
```

## Current coverage

- text normalization
- fuzzy matching
- exact matching
- ambiguity detection
- ambiguity resolution request rewriting
- separation of base vs deluxe titles
- separation of disc vs digital editions

## Current non-coverage

- live Prosody connectivity
- full subprocess-level launcher integration
- console formatting details
- real store integrations

## Expected baseline

A healthy stabilized baseline should pass the test suite before any new integration work begins.
