from mustang_monitor.models import Listing

def test_listing_defaults():
    l = Listing(site="otomoto", listing_id="abc", url="http://x", title="Mustang GT",
                price_eur=8000.0, currency="EUR", mileage_km=120000, year=2001,
                location="Warszawa", description="GT manual coupe")
    assert l.photos == []
    assert l.vin is None
    assert l.transmission is None
    assert l.raw == {}

def test_listing_key():
    l = Listing(site="olx", listing_id="123", url="u", title="t", price_eur=None,
                currency="PLN", mileage_km=None, year=None, location=None, description="")
    assert l.key() == "olx:123"
