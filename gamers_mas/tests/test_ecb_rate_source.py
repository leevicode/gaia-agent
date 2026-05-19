import pytest

from app.currency.ecb_rate_source import ECBRateSource, parse_ecb_usd_rate


VALID_ECB_XML = """<?xml version='1.0' encoding='UTF-8'?>
<gesmes:Envelope xmlns:gesmes='http://www.gesmes.org/xml/2002-08-01'
                 xmlns='http://www.ecb.int/vocabulary/2002-08-01/eurofxref'>
  <Cube>
    <Cube time='2026-05-08'>
      <Cube currency='USD' rate='1.1712'/>
      <Cube currency='GBP' rate='0.8571'/>
    </Cube>
  </Cube>
</gesmes:Envelope>
"""


def test_parse_ecb_usd_rate_converts_eur_usd_to_usd_eur():
    rate = parse_ecb_usd_rate(VALID_ECB_XML)

    assert rate.from_currency == "USD"
    assert rate.to_currency == "EUR"
    assert rate.provider == "ecb"
    assert rate.rate_date == "2026-05-08"
    assert round(rate.rate, 6) == round(1 / 1.1712, 6)
    assert "1 EUR = 1.1712 USD" in rate.raw_rate_note


def test_ecb_rate_source_uses_daily_endpoint_and_timeout():
    requested = {}

    def fake_http_get_text(url: str, timeout_seconds: float) -> str:
        requested["url"] = url
        requested["timeout_seconds"] = timeout_seconds
        return VALID_ECB_XML

    source = ECBRateSource(
        timeout_seconds=5.0,
        http_get_text=fake_http_get_text,
    )

    rate = source.get_usd_to_eur_rate()

    assert "eurofxref-daily.xml" in requested["url"]
    assert requested["timeout_seconds"] == 5.0
    assert rate.from_currency == "USD"
    assert rate.to_currency == "EUR"


def test_parse_ecb_usd_rate_rejects_missing_usd_rate():
    xml_text = VALID_ECB_XML.replace("<Cube currency='USD' rate='1.1712'/>", "")

    with pytest.raises(RuntimeError, match="USD rate"):
        parse_ecb_usd_rate(xml_text)


def test_parse_ecb_usd_rate_rejects_invalid_numeric_rate():
    xml_text = VALID_ECB_XML.replace("rate='1.1712'", "rate='not-a-number'")

    with pytest.raises(RuntimeError, match="not numeric"):
        parse_ecb_usd_rate(xml_text)


def test_ecb_rate_source_rejects_invalid_timeout():
    with pytest.raises(ValueError, match="timeout_seconds"):
        ECBRateSource(timeout_seconds=0)
