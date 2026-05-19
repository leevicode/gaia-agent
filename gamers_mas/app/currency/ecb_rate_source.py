import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable
from urllib.request import Request, urlopen


ECB_DAILY_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_XML_NAMESPACE = "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"
ECB_SOURCE_NAME = "European Central Bank euro foreign exchange reference rates"


@dataclass(frozen=True)
class CurrencyRate:
    from_currency: str
    to_currency: str
    rate: float
    provider: str
    source: str
    rate_date: str
    raw_rate_note: str

    def to_dict(self) -> dict:
        return {
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate": self.rate,
            "provider": self.provider,
            "source": self.source,
            "rate_date": self.rate_date,
            "raw_rate_note": self.raw_rate_note,
        }


def default_http_get_text(url: str, timeout_seconds: float) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "gamers-mas-spade-demo/0.1",
        },
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        status_code = getattr(response, "status", 200)

        if status_code < 200 or status_code >= 300:
            raise RuntimeError(
                f"ECB rate request failed with HTTP status {status_code}."
            )

        return response.read().decode("utf-8")


def parse_ecb_usd_rate(xml_text: str) -> CurrencyRate:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RuntimeError("Invalid ECB XML response.") from exc

    namespaces = {
        "ecb": ECB_XML_NAMESPACE,
    }

    dated_cube = root.find(".//ecb:Cube[@time]", namespaces)
    if dated_cube is None:
        raise RuntimeError("ECB XML response does not contain a rate date.")

    rate_date = dated_cube.attrib.get("time")
    if not rate_date:
        raise RuntimeError("ECB XML response has an empty rate date.")

    usd_cube = dated_cube.find("ecb:Cube[@currency='USD']", namespaces)
    if usd_cube is None:
        raise RuntimeError("ECB XML response does not contain a USD rate.")

    raw_rate = usd_cube.attrib.get("rate")
    if raw_rate is None:
        raise RuntimeError("ECB XML USD rate is missing.")

    try:
        usd_per_eur = float(raw_rate)
    except ValueError as exc:
        raise RuntimeError(f"ECB XML USD rate is not numeric: {raw_rate}.") from exc

    if usd_per_eur <= 0:
        raise RuntimeError("ECB XML USD rate must be greater than 0.")

    usd_to_eur = 1.0 / usd_per_eur

    return CurrencyRate(
        from_currency="USD",
        to_currency="EUR",
        rate=usd_to_eur,
        provider="ecb",
        source=ECB_SOURCE_NAME,
        rate_date=rate_date,
        raw_rate_note=f"ECB XML reports 1 EUR = {usd_per_eur} USD.",
    )


class ECBRateSource:
    def __init__(
        self,
        timeout_seconds: float = 8.0,
        http_get_text: Callable[[str, float], str] = default_http_get_text,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")

        self.timeout_seconds = timeout_seconds
        self.http_get_text = http_get_text

    def get_usd_to_eur_rate(self) -> CurrencyRate:
        xml_text = self.http_get_text(ECB_DAILY_RATES_URL, self.timeout_seconds)
        return parse_ecb_usd_rate(xml_text)
