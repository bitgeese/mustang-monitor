# mustang_monitor/sources/mobilede.py
#
# Actor: 3x1t/mobile-de-scraper-ppr (Pay-per-result, ~$0.30/1k)
# Dataset fields used: id, url, title, price (nested), description, attributes (dict),
#   images, brand, model. attributes typically contains mileage/firstRegistration/fuel.
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "mobilede"


def _price_eur(price_obj, fx):
    """Pull EUR price from common shapes: number, {total: {amount, currency, formatted}}, or string."""
    if isinstance(price_obj, (int, float)):
        return round(float(price_obj), 2)
    if isinstance(price_obj, dict):
        total = price_obj.get("total")
        if isinstance(total, dict):
            amount = total.get("amount")
            currency = total.get("currency") or price_obj.get("currency") or "EUR"
            if isinstance(amount, (int, float)):
                return round(float(amount) * fx.get(currency, 1.0), 2)
            formatted = total.get("formatted")
            if isinstance(formatted, str):
                return parse_price_eur(formatted, fx)
        if isinstance(total, (int, float)):
            return round(float(total) * fx.get(price_obj.get("currency") or "EUR", 1.0), 2)
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
    # mileage: "Kilometerstand" / "mileage"; year: from "firstRegistration" (DD/YYYY or MM/YYYY)
    mileage_v = _attr(attrs, "Kilometerstand", "mileage", "km")
    first_reg = _attr(attrs, "Erstzulassung", "firstRegistration", "First registration")
    mileage = parse_mileage_km(str(mileage_v) if mileage_v is not None else "")
    year = parse_year(str(first_reg) if first_reg is not None else title)
    photos = list(item.get("images") or [])
    if not photos and isinstance(item.get("previewImage"), str):
        photos = [item["previewImage"]]
    return Listing(
        site=SITE,
        listing_id=str(item.get("id") or item.get("url") or ""),
        url=str(item.get("url", "")),
        title=title,
        price_eur=price_eur,
        currency="EUR",
        mileage_km=mileage,
        year=year,
        location=str((item.get("dealerDetails") or {}).get("location") or item.get("location") or "") or None,
        description=desc,
        photos=photos,
        vin=extract_vin(f"{title} {desc}"),
        raw=item,
    )
