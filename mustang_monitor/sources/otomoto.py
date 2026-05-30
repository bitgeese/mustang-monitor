# mustang_monitor/sources/otomoto.py
#
# Actor: automation-lab/otomoto-scraper (Pay-per-event, ~$0.60/1k)
# Dataset fields used: id, url, title, year (int), mileageKm (int), pricePLN (int),
#   city, region, description (optional), images/thumbnails (list).
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "otomoto"


def _as_int(v):
    return v if isinstance(v, int) else None


def map_item(item: dict, fx: dict) -> Listing:
    title = str(item.get("title", "") or "")
    desc = str(item.get("description", "") or "")
    # year & mileage are numeric in this actor's schema; fall back to parse_* if absent
    year = _as_int(item.get("year")) or parse_year(title)
    mileage = _as_int(item.get("mileageKm")) or parse_mileage_km(str(item.get("mileageKm") or ""))
    # price is numeric PLN; convert to EUR via fx
    price_pln = item.get("pricePLN")
    if isinstance(price_pln, (int, float)):
        price_eur = round(float(price_pln) * fx.get("PLN", 1.0), 2)
    else:
        price_eur = parse_price_eur(str(price_pln or "") + " PLN", fx)
    city = item.get("city") or ""
    region = item.get("region") or ""
    location = ", ".join(p for p in (city, region) if p) or None
    photos = list(item.get("images") or item.get("thumbnails") or [])
    return Listing(
        site=SITE,
        listing_id=str(item.get("id") or item.get("url") or ""),
        url=str(item.get("url", "")),
        title=title,
        price_eur=price_eur,
        currency="PLN",
        mileage_km=mileage,
        year=year,
        location=location,
        description=desc,
        photos=photos,
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
