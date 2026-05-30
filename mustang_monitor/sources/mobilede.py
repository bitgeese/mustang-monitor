# mustang_monitor/sources/mobilede.py
#
# Actor: 3x1t/mobile-de-scraper-ppr (Pay-per-result, ~$0.30/1k)
# Real dataset shape (live-verified 2026-05-30):
#   id (int), url, title, description, images (list), previewImage,
#   price = { total: { amount, currency, localized }, type },
#   attributes = { "First Registration": "MM/YYYY", "Mileage": "72,000 km",
#                  "Transmission": "Automatic"|"Manual"|..., "Category": "Sports Car/Coupe",
#                  "Cubic Capacity": "1,984 ccm", "Cylinders": "4", ... },
#   brand, model, segment, category, dealerDetails.
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "mobilede"


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
            for text_key in ("localized", "formatted"):
                txt = total.get(text_key)
                if isinstance(txt, str):
                    return parse_price_eur(txt, fx)
        if isinstance(total, (int, float)):
            return round(float(total) * fx.get(price_obj.get("currency") or "EUR", 1.0), 2)
        for text_key in ("localized", "formatted"):
            txt = price_obj.get(text_key)
            if isinstance(txt, str):
                return parse_price_eur(txt, fx)
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


def _normalise_transmission(v: str | None) -> str | None:
    if not v:
        return None
    s = str(v).strip().lower()
    if "manual" in s or "schalt" in s:
        return "manual"
    if "auto" in s or "tiptronic" in s or "dsg" in s:
        return "automatic"
    return None


def map_item(item: dict, fx: dict) -> Listing:
    title = str(item.get("title") or item.get("name") or "")
    desc_raw = str(item.get("description", "") or "")
    attrs = item.get("attributes") or {}
    price_eur = _price_eur(item.get("price"), fx)

    mileage_v = _attr(attrs, "Mileage", "Kilometerstand", "km")
    mileage = parse_mileage_km(str(mileage_v) if mileage_v is not None else "")

    first_reg = _attr(attrs, "First Registration", "Erstzulassung", "firstRegistration")
    year = parse_year(str(first_reg) if first_reg is not None else title)

    trans_raw = _attr(attrs, "Transmission", "Getriebe")
    transmission = _normalise_transmission(trans_raw)

    category = _attr(attrs, "Category", "Kategorie") or item.get("category") or ""
    # Fold structured fields into description so the rules gate (convertible/automatic) sees them.
    description = " | ".join(p for p in [
        desc_raw[:600],   # cap raw description to keep prompts small
        f"Category: {category}" if category else "",
        f"Transmission: {trans_raw}" if trans_raw else "",
    ] if p)

    photos = list(item.get("images") or [])
    if not photos and isinstance(item.get("previewImage"), str):
        photos = [item["previewImage"]]

    dealer = item.get("dealerDetails") or {}
    location = dealer.get("address") or dealer.get("location") or item.get("location")

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
        description=description,
        photos=photos,
        vin=extract_vin(f"{title} {desc_raw}"),
        transmission=transmission,
        raw=item,
    )
