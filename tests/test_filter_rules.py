from mustang_monitor.models import Listing
from mustang_monitor.filter_rules import passes_hard_filters

SPEC = {
    "years": {"min": 1999, "max": 2004},
    "price_eur": {"min": 4000, "max": 26000},
    "mileage_km": {"min": 0, "max": 220000},
    "keywords": {
        "convertible": ["convertible", "cabrio", "kabriolet"],
        "automatic": ["automatic", "automat", "automatik"],
        "salvage": ["salvage", "powypadkowy", "unfallwagen"],
    },
}

def _mk(**kw):
    base = dict(site="s", listing_id="1", url="u", title="Ford Mustang GT", price_eur=8000.0,
               currency="EUR", mileage_km=120000, year=2001, location="x", description="manual coupe")
    base.update(kw)
    return Listing(**base)

def test_good_listing_passes():
    ok, reasons = passes_hard_filters(_mk(), SPEC)
    assert ok and reasons == []

def test_year_out_of_range_rejected():
    ok, reasons = passes_hard_filters(_mk(year=1996), SPEC)
    assert not ok and any("year" in r for r in reasons)

def test_price_over_band_rejected():
    ok, reasons = passes_hard_filters(_mk(price_eur=30000.0), SPEC)
    assert not ok and any("price" in r for r in reasons)

def test_convertible_keyword_rejected():
    ok, reasons = passes_hard_filters(_mk(title="Mustang GT Cabrio"), SPEC)
    assert not ok and any("convertible" in r for r in reasons)

def test_automatic_keyword_rejected():
    ok, reasons = passes_hard_filters(_mk(description="automatik, full options"), SPEC)
    assert not ok and any("automatic" in r for r in reasons)

def test_salvage_keyword_rejected():
    ok, reasons = passes_hard_filters(_mk(description="auto powypadkowy"), SPEC)
    assert not ok and any("salvage" in r for r in reasons)

def test_missing_year_not_hard_rejected():
    # ambiguous -> let it through to VIN/AI rather than reject
    ok, reasons = passes_hard_filters(_mk(year=None), SPEC)
    assert ok
