# mustang_monitor/sources/otomoto.py
#
# Actor: automation-lab/otomoto-scraper (Pay-per-event, ~$0.60/1k)
# Real dataset keys (live-verified 2026-05-30):
#   id, url, title, shortDescription, make, model, version, year (int),
#   mileageKm (int), fuelType, gearbox ("Manualna"|"Automatyczna"),
#   engineCapacityCc, enginePowerHp, pricePLN (int), priceCurrency,
#   city, region, badges, sellerType, thumbnailUrl, createdAt.
from __future__ import annotations
from mustang_monitor.models import Listing
from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year
from mustang_monitor.vin import extract_vin

SITE = "otomoto"

_GEARBOX_MANUAL = {"manualna", "manual"}
_GEARBOX_AUTO = {"automatyczna", "automat", "automatic"}


def _normalise_transmission(gearbox: str | None) -> str | None:
    if not gearbox:
        return None
    g = gearbox.strip().lower()
    if g in _GEARBOX_MANUAL:
        return "manual"
    if g in _GEARBOX_AUTO:
        return "automatic"
    return None


def map_item(item: dict, fx: dict) -> Listing:
    title = str(item.get("title", "") or "")
    short_desc = str(item.get("shortDescription", "") or "")
    gearbox = item.get("gearbox") or ""
    version = item.get("version") or ""
    fuel = item.get("fuelType") or ""
    # Fold structured fields into a single description string so the rules gate
    # (convertible/automatic/salvage keywords) and the AI scorer can see them.
    description = " | ".join(p for p in [
        short_desc,
        f"Gearbox: {gearbox}" if gearbox else "",
        f"Trim: {version}" if version else "",
        f"Engine: {item.get('engineCapacityCc','')}cc {item.get('enginePowerHp','')}hp",
        f"Fuel: {fuel}" if fuel else "",
    ] if p)

    year = item.get("year") if isinstance(item.get("year"), int) else parse_year(title)
    mileage = item.get("mileageKm") if isinstance(item.get("mileageKm"), int) \
        else parse_mileage_km(str(item.get("mileageKm") or ""))
    price_pln = item.get("pricePLN")
    if isinstance(price_pln, (int, float)):
        price_eur = round(float(price_pln) * fx.get("PLN", 1.0), 2)
    else:
        price_eur = parse_price_eur(str(price_pln or "") + " PLN", fx)

    thumb = item.get("thumbnailUrl")
    photos = [thumb] if isinstance(thumb, str) and thumb else []
    location = ", ".join(p for p in (item.get("city") or "", item.get("region") or "") if p) or None

    return Listing(
        site=SITE,
        listing_id=str(item.get("id") or item.get("url") or ""),
        url=str(item.get("url", "")),
        title=title,
        price_eur=price_eur,
        currency=str(item.get("priceCurrency") or "PLN"),
        mileage_km=mileage,
        year=year,
        location=location,
        description=description,
        photos=photos,
        vin=extract_vin(f"{title} {short_desc}"),
        transmission=_normalise_transmission(gearbox),
        raw=item,
    )
