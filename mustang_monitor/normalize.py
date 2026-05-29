from __future__ import annotations
import re

_CURRENCY_HINT = [("zł", "PLN"), ("pln", "PLN"), ("€", "EUR"), ("eur", "EUR"), ("£", "GBP"), ("gbp", "GBP")]

def _digits(text: str) -> str:
    # keep digits only after stripping thousands separators (space, ., ,)
    return re.sub(r"[^\d]", "", text)

def parse_price_eur(text: str | None, fx: dict) -> float | None:
    if not text:
        return None
    low = text.lower()
    currency = "EUR"
    for hint, code in _CURRENCY_HINT:
        if hint in low:
            currency = code
            break
    num = _digits(low)
    if not num:
        return None
    rate = fx.get(currency, 1.0)
    return round(int(num) * rate, 2)

def parse_mileage_km(text: str | None) -> int | None:
    if not text:
        return None
    low = text.lower()
    if "tys" in low:  # thousands shorthand, e.g. "98 tys. km"
        m = re.search(r"(\d+)", low)
        return int(m.group(1)) * 1000 if m else None
    num = _digits(low)
    return int(num) if num else None

def parse_year(text: str | None) -> int | None:
    if not text:
        return None
    for m in re.findall(r"(19\d{2}|20\d{2})", text):
        y = int(m)
        if 1990 <= y <= 2010:
            return y
    return None
