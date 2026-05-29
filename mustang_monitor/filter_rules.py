from __future__ import annotations
from mustang_monitor.models import Listing

def _haystack(listing: Listing) -> str:
    return f"{listing.title} {listing.description}".lower()

def _has_keyword(text: str, words: list[str]) -> str | None:
    for w in words:
        if w.lower() in text:
            return w
    return None

def passes_hard_filters(listing: Listing, spec: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    text = _haystack(listing)
    kw = spec["keywords"]

    # Negative keywords -> hard reject
    hit = _has_keyword(text, kw["convertible"])
    if hit:
        reasons.append(f"convertible keyword: {hit}")
    hit = _has_keyword(text, kw["automatic"])
    if hit:
        reasons.append(f"automatic keyword: {hit}")
    hit = _has_keyword(text, kw["salvage"])
    if hit:
        reasons.append(f"salvage keyword: {hit}")

    # Numeric bands -> reject only when value is known and out of range
    y = spec["years"]
    if listing.year is not None and not (y["min"] <= listing.year <= y["max"]):
        reasons.append(f"year out of range: {listing.year}")
    p = spec["price_eur"]
    if listing.price_eur is not None and not (p["min"] <= listing.price_eur <= p["max"]):
        reasons.append(f"price out of band: {listing.price_eur}")
    m = spec["mileage_km"]
    if listing.mileage_km is not None and not (m["min"] <= listing.mileage_km <= m["max"]):
        reasons.append(f"mileage out of band: {listing.mileage_km}")

    return (len(reasons) == 0, reasons)
