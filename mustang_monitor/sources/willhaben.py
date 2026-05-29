# mustang_monitor/sources/willhaben.py
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "willhaben"


def map_item(item: dict, fx: dict) -> Listing:
    desc = item.get("description", "") or ""
    title = item.get("title", "") or item.get("name", "") or ""
    price_text = f"{item.get('price', '')} {item.get('currency', 'EUR')}"
    return Listing(
        site=SITE,
        listing_id=str(item.get("id") or item.get("adId")),
        url=item.get("url", "") or item.get("link", ""),
        title=title,
        price_eur=parse_price_eur(price_text, fx),
        currency=item.get("currency", "EUR"),
        mileage_km=parse_mileage_km(str(item.get("mileage", ""))),
        year=parse_year(str(item.get("year") or title)),
        location=item.get("location"),
        description=desc,
        photos=list(item.get("photos", []) or item.get("images", []) or []),
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
