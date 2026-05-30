# mustang_monitor/sources/olx.py
#
# Actor: 123webdata/olx-scraper (Pay-per-result, $5/1k)
# Dataset fields used: url, name (title), price, currency, images, description, attributes.
# attributes is a dict possibly containing "Rok produkcji", "Przebieg", etc. (Polish OLX).
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "olx"


def _attr_lookup(attrs, *candidates):
    """Look up a value in attributes dict by trying multiple key spellings."""
    if not isinstance(attrs, dict):
        return None
    for k in candidates:
        for key, val in attrs.items():
            if str(key).strip().lower() == k.lower():
                return val
    return None


def map_item(item: dict, fx: dict) -> Listing:
    title = str(item.get("name") or item.get("title") or "")
    desc = str(item.get("description", "") or "")
    attrs = item.get("attributes") or {}
    currency = item.get("currency") or "PLN"
    price_text = f"{item.get('price', '')} {currency}"
    price_eur = parse_price_eur(price_text, fx)
    # year / mileage from attributes (OLX uses Polish labels); fall back to text
    year_attr = _attr_lookup(attrs, "Rok produkcji", "Year", "Rok")
    mileage_attr = _attr_lookup(attrs, "Przebieg", "Mileage")
    year = parse_year(str(year_attr) if year_attr is not None else title)
    mileage = parse_mileage_km(str(mileage_attr) if mileage_attr is not None else "")
    return Listing(
        site=SITE,
        listing_id=str(item.get("sku") or item.get("id") or item.get("url") or ""),
        url=str(item.get("url", "")),
        title=title,
        price_eur=price_eur,
        currency=currency,
        mileage_km=mileage,
        year=year,
        location=str(item.get("location") or item.get("city") or "") or None,
        description=desc,
        photos=list(item.get("images") or []),
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
