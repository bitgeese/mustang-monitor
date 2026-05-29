import json
from pathlib import Path
from mustang_monitor.sources.otomoto import map_item

FX = {"PLN": 0.23, "EUR": 1.0}

def test_otomoto_map_item():
    raw = json.loads(Path("tests/fixtures/otomoto_item.json").read_text())
    listing = map_item(raw, FX)
    assert listing.site == "otomoto"
    assert listing.listing_id == "ID6abc"
    assert listing.year == 2001
    assert listing.mileage_km == 138000
    assert listing.price_eur == round(39900 * 0.23, 2)
    assert listing.vin == "1FAFP42X11F123456"
    assert listing.photos == ["https://img.otomoto/1.jpg", "https://img.otomoto/2.jpg"]

def test_run_apify_passes_input(monkeypatch):
    from mustang_monitor.sources import base
    captured = {}
    class FakeRun:
        def call(self, run_input):
            captured["input"] = run_input
            return {"defaultDatasetId": "ds1"}
    class FakeDataset:
        def iterate_items(self):
            yield {"id": "x"}
    class FakeClient:
        def actor(self, actor_id):
            captured["actor"] = actor_id
            return FakeRun()
        def dataset(self, ds_id):
            return FakeDataset()
    items = list(base.run_apify(FakeClient(), "acme/actor", {"maxItems": 5}))
    assert captured["actor"] == "acme/actor"
    assert captured["input"] == {"maxItems": 5}
    assert items == [{"id": "x"}]
