from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.currency.ecb_rate_source import CurrencyRate, ECBRateSource


@dataclass(frozen=True)
class ConversionResult:
    original_amount: float
    original_currency: str
    converted_amount: float
    converted_currency: str
    conversion_rate: float
    conversion_rate_provider: str
    conversion_rate_source: str
    conversion_rate_date: str
    conversion_note: str

    def to_dict(self) -> dict:
        return {
            "original_amount": self.original_amount,
            "original_currency": self.original_currency,
            "converted_amount": self.converted_amount,
            "converted_currency": self.converted_currency,
            "conversion_rate": self.conversion_rate,
            "conversion_rate_provider": self.conversion_rate_provider,
            "conversion_rate_source": self.conversion_rate_source,
            "conversion_rate_date": self.conversion_rate_date,
            "conversion_note": self.conversion_note,
        }


def parse_positive_float(value: Any, field_name: str) -> float:
    try:
        parsed_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc

    if parsed_value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")

    return parsed_value


def build_configured_usd_to_eur_rate(
    usd_to_eur_rate: Any,
    source: str,
    rate_date: str,
) -> CurrencyRate:
    parsed_rate = parse_positive_float(usd_to_eur_rate, "usd_to_eur_rate")

    if not source or not str(source).strip():
        raise ValueError("source must not be empty.")

    if not rate_date or not str(rate_date).strip():
        raise ValueError("rate_date must not be empty.")

    return CurrencyRate(
        from_currency="USD",
        to_currency="EUR",
        rate=parsed_rate,
        provider="configured_fallback",
        source=str(source).strip(),
        rate_date=str(rate_date).strip(),
        raw_rate_note=(
            f"Configured fallback reports 1 USD = {parsed_rate} EUR."
        ),
    )


def resolve_usd_to_eur_rate(
    rate_provider: str,
    timeout_seconds: float,
    allow_fallback_rate: bool,
    fallback_usd_to_eur_rate: Any,
    fallback_rate_source: str,
    fallback_rate_date: str,
    ecb_rate_source: ECBRateSource | None = None,
) -> CurrencyRate:
    provider = str(rate_provider or "ecb").strip().lower()

    if provider == "configured":
        return build_configured_usd_to_eur_rate(
            usd_to_eur_rate=fallback_usd_to_eur_rate,
            source=fallback_rate_source,
            rate_date=fallback_rate_date,
        )

    if provider != "ecb":
        raise ValueError(
            f"Unsupported currency rate provider: {rate_provider}."
        )

    try:
        source = ecb_rate_source or ECBRateSource(
            timeout_seconds=timeout_seconds,
        )
        return source.get_usd_to_eur_rate()
    except Exception as exc:
        if not allow_fallback_rate:
            raise RuntimeError(
                "ECB currency conversion failed and fallback is disabled."
            ) from exc

        return build_configured_usd_to_eur_rate(
            usd_to_eur_rate=fallback_usd_to_eur_rate,
            source=fallback_rate_source,
            rate_date=fallback_rate_date,
        )


def convert_usd_to_eur_amount(price_usd: Any, rate: CurrencyRate) -> ConversionResult:
    parsed_price_usd = parse_positive_float(price_usd, "price_usd")

    if rate.from_currency != "USD" or rate.to_currency != "EUR":
        raise ValueError("rate must convert from USD to EUR.")

    converted_price_eur = round(parsed_price_usd * rate.rate, 2)

    return ConversionResult(
        original_amount=parsed_price_usd,
        original_currency="USD",
        converted_amount=converted_price_eur,
        converted_currency="EUR",
        conversion_rate=rate.rate,
        conversion_rate_provider=rate.provider,
        conversion_rate_source=rate.source,
        conversion_rate_date=rate.rate_date,
        conversion_note=(
            f"Converted from {parsed_price_usd:.2f} USD to {converted_price_eur:.2f} EUR "
            f"using {rate.source}; rate: 1 USD = {rate.rate:.6f} EUR; "
            f"rate date: {rate.rate_date}."
        ),
    )


def apply_usd_to_eur_conversion_to_deal(
    deal: dict[str, Any],
    rate: CurrencyRate,
) -> dict[str, Any]:
    converted_deal = deepcopy(deal)

    price_usd = converted_deal.get("price_usd")
    currency = str(converted_deal.get("currency", "")).upper()

    if currency != "USD" or price_usd is None:
        converted_deal["currency_conversion_applied"] = False
        return converted_deal

    conversion = convert_usd_to_eur_amount(
        price_usd=price_usd,
        rate=rate,
    )

    converted_deal["price_eur"] = conversion.converted_amount
    converted_deal["original_price_usd"] = conversion.original_amount
    converted_deal["original_currency"] = conversion.original_currency
    converted_deal["converted_currency"] = conversion.converted_currency
    converted_deal["currency_conversion_applied"] = True
    converted_deal["conversion_rate"] = conversion.conversion_rate
    converted_deal["conversion_rate_provider"] = conversion.conversion_rate_provider
    converted_deal["conversion_rate_source"] = conversion.conversion_rate_source
    converted_deal["conversion_rate_date"] = conversion.conversion_rate_date
    converted_deal["conversion_note"] = conversion.conversion_note
    converted_deal["currency_note"] = conversion.conversion_note

    return converted_deal


def apply_usd_to_eur_conversion_to_deals(
    deals: list[dict[str, Any]],
    rate: CurrencyRate,
) -> list[dict[str, Any]]:
    return [
        apply_usd_to_eur_conversion_to_deal(deal, rate)
        for deal in deals
    ]
