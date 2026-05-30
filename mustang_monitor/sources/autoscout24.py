# mustang_monitor/sources/autoscout24.py
#
# Actor: 3x1t/autoscout24-scraper-ppr (Pay-per-result, $1.29/1k)
# Dataset fields used: id, url, title, brand, model, modelVersion, vehicleType, bodyType,
#   price (with total.amount, total.currency, formatted), description, attributes (dict),
#   features, images, previewImage, createdDate, dealerDetails.
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "autoscout24"


def _price_eur(price_obj, fx):
    if isinstance(price_obj, (int, float)):
        return round(float(price_obj), 2)
    if isinstance(price_obj, dict):
        total = price_obj.get("total")
        if isinstance(total, dict):
            amount = total.get("amount")
            currency = total.get("currency") or "EUR"
            if isinstance(amount, (int, float)):
                return round(float(amount) * fx.get(currency, 1.0), 2)
            formatted = total.get("formatted") or price_obj.get("formatted")
            if isinstance(formatted, str):
                return parse_price_eur(formatted, fx)
        formatted = price_obj.get("formatted")
        if isinstance(formatted, str):
            return parse_price_eur(formatted, fx)
    if isinstance(price_obj, str):
        return parse_price_eur(price_obj, fx)
    return None


def _attr(attrs, *names):
    if not isinstance(attrs, dict):
        return None
    for n in names:
        for k, v in attrs.items():
            if str(k).strip().lower() == n.lower():
                return v
    return None


def map_item(item: dict, fx: dict) -> Listing:
    title = str(item.get("title") or item.get("name") or "")
    desc = str(item.get("description", "") or "")
    attrs = item.get("attributes") or {}
    price_eur = _price_eur(item.get("price"), fx)
    mileage_v = _attr(attrs, "mileage", "Kilometerstand", "km")
    first_reg = _attr(attrs, "firstRegistration", "Erstzulassung", "First registration")
    mileage = parse_mileage_km(str(mileage_v) if mileage_v is not None else "")
    year = parse_year(str(first_reg) if first_reg is not None else title)
    photos = list(item.get("images") or [])
    if not photos and isinstance(item.get("previewImage"), str):
        photos = [item["previewImage"]]
    dealer = item.get("dealerDetails") or {}
    location = dealer.get("location") or dealer.get("address") or item.get("location")
    body_class = str(item.get("bodyType") or item.get("vehicleType") or "")
    body_hint_text = f"{title} {body_class} {desc}"
    return Listing(
        site=SITE,
        listing_id=str(item.get("id") or item.get("url") or ""),
        url=str(item.get("url", "")),
        title=title,
        price_eur=price_eur,
        currency="EUR",
        mileage_km=mileage,
        year=year,
        location=str(location) if location else None,
        # Stuff bodyType into description so the convertible/cabriolet rules gate sees it.
        description=body_hint_text,
        photos=photos,
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
