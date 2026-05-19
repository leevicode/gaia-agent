# Source Integration

This document explains how the project uses mock data, CheapShark, and European Central Bank currency conversion.

## Source integration summary

The project uses two kinds of data sources:

1. **Mock sources**
   - deterministic
   - always available
   - used for local console, official store, gray-market, and fallback behavior

2. **Live sources**
   - CheapShark for online PC game deals
   - European Central Bank for USD to EUR exchange-rate reference data

CheapShark is active by default for the software scenario. Mock authorized reseller data is still used as fallback if CheapShark fails or returns no usable exact-title deal.

## Source adapter design

Source adapters live in:

```text
app/sources/
```

| File | Purpose |
|---|---|
| `base.py` | Defines the common `DealSource` interface |
| `mock_sources.py` | Implements mock source adapters |
| `cheapshark_source.py` | Implements live CheapShark source adapter |

The shared source interface is:

```python
source.search_deals(title, **filters)
```

This keeps source-specific API logic outside the agents.

## Mock source adapters

Mock adapters wrap `app/mock_data.py`.

They are:

```text
MockOfficialStoreSource
MockAuthorizedResellerSource
MockGrayMarketSource
MockMarketplaceSource
```

Mock data is used for:

- official software deals
- official console deals
- gray-market warning examples
- local marketplace examples
- fallback authorized reseller results

## CheapShark source

CheapShark is used by:

```text
AuthorizedResellerAgent
```

for the software scenario only.

The source file is:

```text
app/sources/cheapshark_source.py
```

The base API URL is:

```text
https://www.cheapshark.com/api/1.0
```

## CheapShark is global, not local

CheapShark provides online PC game deal data. It does not provide local store listings.

Fields such as:

```text
dealID
storeID
gameID
steamAppID
```

are API identifiers or store/game identifiers. They are not activation keys, coupon codes, or local listing codes.

The project does not claim that every CheapShark deal is region-free. It does not verify activation-region restrictions.

## Exact CheapShark gameID lookup

The project does not rely on broad `/deals?title=...` lookup as the final truth.

The safe flow is:

```text
resolved project title
-> query CheapShark games endpoint
-> find exact matching CheapShark title
-> get exact CheapShark gameID
-> fetch details and deals for that gameID
-> map only those deals
```

This prevents the base game from being mixed with:

```text
Deluxe Pack
Digital Deluxe
DLC
related products
different editions
```

Example:

```text
Resolved title: Crimson Desert
Accepted: Crimson Desert
Rejected: Crimson Desert Deluxe Pack
Rejected: Crimson Desert Digital Deluxe
```

## CheapShark fallback behavior

The authorized reseller agent uses BDI reasoning to choose the source plan.

Possible plans:

```text
query_real_source
fallback_to_mock_source
use_mock_source
return_no_results
```

Default behavior:

```text
USE_REAL_CHEAPSHARK=true
```

If CheapShark succeeds and returns exact-title deals:

```text
selected_plan: query_real_source
```

If CheapShark fails or returns no usable exact-title deals:

```text
selected_plan: fallback_to_mock_source
```

If CheapShark is disabled:

```text
selected_plan: use_mock_source
```

## Currency problem

CheapShark prices are USD. The rest of the project ranks deals in EUR.

The project must not compare USD as if it were EUR.

Earlier safe behavior was:

```text
show USD deals separately
do not rank them against EUR deals
```

The final behavior is better:

```text
convert CheapShark USD prices to EUR
keep original USD price
show conversion rate and source
rank converted EUR prices with other legitimate EUR deals
```

## ECB currency conversion

Currency conversion code lives in:

```text
app/currency/
```

| File | Purpose |
|---|---|
| `ecb_rate_source.py` | Fetches and parses the ECB daily XML rate |
| `converter.py` | Applies USD to EUR conversion and writes metadata |

The ECB endpoint used is:

```text
https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
```

The ECB XML expresses rates as:

```text
1 EUR = X USD
```

For conversion:

```text
1 USD = 1 / X EUR
price_eur = price_usd / X
```

The output shows the rate as:

```text
1 USD = 0.xxxxxx EUR
```

## Conversion metadata

A converted CheapShark deal contains fields like:

```text
price_usd
original_price_usd
price_eur
currency_conversion_applied
conversion_rate
conversion_rate_source
conversion_rate_date
currency
currency_note
```

Example output:

```text
Recommended legitimate deal: Fanatical - EUR51.07 | converted from 59.49 USD | 1 USD = 0.858516 EUR | rate source=European Central Bank euro foreign exchange reference rates | rate date=2026-05-18 | trust=0.8 | type=authorized_reseller
```

## Fallback currency rate

The project keeps a configured fallback rate in `.env`.

Default:

```text
ALLOW_CURRENCY_FALLBACK_RATE=true
FALLBACK_USD_TO_EUR_RATE=0.92
FALLBACK_USD_TO_EUR_RATE_SOURCE=manual_fallback_rate
FALLBACK_USD_TO_EUR_RATE_DATE=2026-05-08
```

This fallback exists so the demo can still run if ECB is temporarily unavailable.

The fallback rate is not hardcoded in Python code. It is configured in `.env` and `.env.example`.

## Environment variables

Source and conversion configuration lives in:

```text
.env
.env.example
```

Relevant variables:

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

## Important configuration behavior

### CheapShark enabled and ECB enabled

```text
USE_REAL_CHEAPSHARK=true
ENABLE_CURRENCY_CONVERSION=true
```

Behavior:

- CheapShark is queried.
- USD prices are converted to EUR.
- Converted CheapShark deals can win recommendation ranking.

### CheapShark enabled and conversion disabled

```text
USE_REAL_CHEAPSHARK=true
ENABLE_CURRENCY_CONVERSION=false
```

Behavior:

- CheapShark is queried.
- USD deals are shown separately.
- USD deals are not ranked with EUR deals.

### CheapShark disabled

```text
USE_REAL_CHEAPSHARK=false
```

Behavior:

- Authorized reseller agent uses mock authorized reseller data.
- No live CheapShark call is made.

### ECB unavailable and fallback allowed

```text
ALLOW_CURRENCY_FALLBACK_RATE=true
```

Behavior:

- fallback rate from `.env` is used.
- output should identify the fallback rate source.

### ECB unavailable and fallback disabled

```text
ALLOW_CURRENCY_FALLBACK_RATE=false
```

Behavior:

- conversion cannot be applied.
- CheapShark deals may become foreign-currency deals or source fallback may occur depending on the code path.

## Manual CheapShark smoke test

Use:

```bash
python scripts/live_cheapshark_smoke_test.py "Crimson Desert"
```

This script is for manual verification only. It is not part of the automated test suite because live API calls can fail.

## Why live APIs are not used in pytest

Normal tests use fake CheapShark and ECB responses.

Reason:

- tests must be deterministic
- tests must work offline
- live APIs may be temporarily unavailable
- prices and exchange rates change over time

Manual runtime tests are used to show live behavior for the report.

## Source integration limitations

The source integration has deliberate limits:

- only software titles in the internal catalog can be searched
- CheapShark is not used as arbitrary title discovery for unknown games
- local console scenario remains mock-based
- gray-market data remains mock-based
- region lock and activation restrictions are not verified
- ECB rates are informational reference rates, not guaranteed transaction rates
- no purchasing or payment happens

