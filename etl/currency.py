"""Single source of truth for currency conversion (base: ILS).

Replaces the hardcoded rate tables that used to live inside scraper.py and
scraper_playwright.py, and mirrors currency_converter.py without the
streamlit dependency. Rates come from exchangerate-api.com, are cached on
disk for 24h, and are persisted to the fx_rates table when a DB connection
is available.
"""
import json
import logging
import os
import time

import requests

FALLBACK_RATES = {
    "ILS": 1.00,
    "USD": 3.20,
    "EUR": 3.95,
    "GBP": 4.65,
    "CAD": 2.60,
    "AUD": 2.35,
}

_CACHE_PATH = os.path.join(os.path.dirname(__file__), ".cache", "fx_rates.json")
_CACHE_TTL = 86400  # 24h


def get_rates() -> dict:
    """ILS-based conversion rates, cached on disk for 24 hours."""
    try:
        with open(_CACHE_PATH) as fh:
            cached = json.load(fh)
        if time.time() - cached["fetched_at"] < _CACHE_TTL:
            return cached["rates"]
    except (OSError, ValueError, KeyError):
        pass

    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5
        )
        response.raise_for_status()
        data = response.json()
        usd_to_ils = data["rates"].get("ILS", 3.60)
        rates = {
            "ILS": 1.00,
            "USD": usd_to_ils,
            "EUR": data["rates"].get("EUR", 0.95) * usd_to_ils,
            "GBP": data["rates"].get("GBP", 0.82) * usd_to_ils,
            "CAD": data["rates"].get("CAD", 1.35) * usd_to_ils,
            "AUD": data["rates"].get("AUD", 1.52) * usd_to_ils,
        }
    except Exception as exc:  # noqa: BLE001 - any network failure -> fallback
        logging.warning("Currency API failed (%s); using fallback rates", exc)
        return FALLBACK_RATES

    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    with open(_CACHE_PATH, "w") as fh:
        json.dump({"fetched_at": time.time(), "rates": rates}, fh)
    return rates


def convert_to_ils(amount: float, currency_code: str) -> float:
    rate = get_rates().get(currency_code.upper(), 1.0)
    return round(amount * rate, 2)


def detect_currency(price_text: str) -> str:
    """Map a BrickLink price-cell string (e.g. 'US $12.34') to a currency code.

    Order matters: country prefixes are checked before the bare '$' fallback,
    matching the behavior previously hardcoded in both scrapers.
    """
    p = price_text.upper()
    if "ILS" in p or "₪" in p:
        return "ILS"
    if "US" in p:
        return "USD"
    if "CA" in p:
        return "CAD"
    if "AU" in p:
        return "AUD"
    if "EU" in p or "€" in p:
        return "EUR"
    if "GB" in p or "£" in p:
        return "GBP"
    if "$" in p:
        return "USD"
    return "ILS"


def persist_rates(conn) -> None:
    """Store today's rates in fx_rates (idempotent per day)."""
    rates = get_rates()
    with conn.cursor() as cur:
        for code, rate in rates.items():
            cur.execute(
                """
                insert into fx_rates (currency, rate_to_ils, fetched_on)
                values (%s, %s, current_date)
                on conflict (currency, fetched_on) do update
                    set rate_to_ils = excluded.rate_to_ils
                """,
                (code, rate),
            )
