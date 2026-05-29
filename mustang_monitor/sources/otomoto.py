# mustang_monitor/sources/otomoto.py
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "otomoto"


def map_item(item: dict, fx: dict) -> Listing:
    desc = item.get("description", "") or ""
    title = item.get("title", "") or ""
    price_text = f"{item.get('price', '')} {item.get('currency', '')}"
    return Listing(
        site=SITE,
        listing_id=str(item.get("id")),
        url=item.get("url", ""),
        title=title,
        price_eur=parse_price_eur(price_text, fx),
        currency=item.get("currency", "PLN"),
        mileage_km=parse_mileage_km(item.get("mileage")),
        year=parse_year(item.get("year") or title),
        location=item.get("location"),
        description=desc,
        photos=list(item.get("photos", []) or []),
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
