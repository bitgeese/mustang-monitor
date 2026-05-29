from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Listing:
    site: str
    listing_id: str
    url: str
    title: str
    price_eur: float | None
    currency: str
    mileage_km: int | None
    year: int | None
    location: str | None
    description: str
    photos: list[str] = field(default_factory=list)
    vin: str | None = None
    transmission: str | None = None  # "manual" | "automatic" | None
    raw: dict = field(default_factory=dict)

    def key(self) -> str:
        return f"{self.site}:{self.listing_id}"
