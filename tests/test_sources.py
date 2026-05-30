import json
from pathlib import Path
from mustang_monitor.sources.otomoto import map_item as otomoto_map
from mustang_monitor.sources.mobilede import map_item as mobilede_map

FX = {"PLN": 0.23, "EUR": 1.0}
FIXTURES = Path(__file__).parent / "fixtures"

def test_otomoto_map_item():
    raw = json.loads((FIXTURES / "otomoto_item.json").read_text())
    listing = otomoto_map(raw, FX)
    assert listing.site == "otomoto"
    assert listing.listing_id == "6147784510"
    assert listing.year == 2001
    assert listing.mileage_km == 138000
    assert listing.price_eur == round(39900 * 0.23, 2)
    assert listing.currency == "PLN"
    assert listing.location == "Warszawa, Mazowieckie"
    assert listing.vin == "1FAFP42X11F123456"
    assert listing.photos == ["https://img.otomoto/1.jpg"]
    assert listing.transmission == "manual"
    assert "Gearbox: Manualna" in listing.description
    assert "Trim: GT" in listing.description

def test_mobilede_map_item():
    raw = json.loads((FIXTURES / "mobilede_item.json").read_text())
    listing = mobilede_map(raw, FX)
    assert listing.site == "mobilede"
    assert listing.listing_id == "456657552"
    assert listing.year == 2001
    assert listing.mileage_km == 138000
    assert listing.price_eur == 9180.0
    assert listing.currency == "EUR"
    assert listing.transmission == "manual"
    assert "Category: Sports Car/Coupe" in listing.description
    assert listing.vin == "1FAFP42X11F123456"
    assert listing.photos[0] == "https://img.classistatic.de/1.jpg"

# Fakes mirror the real apify-client 3.x interface: keyword-only `call(run_input=...)`
# returning a Run-like object with `.default_dataset_id` (or None on timeout).
class _FakeRunResult:
    def __init__(self, dataset_id):
        self.default_dataset_id = dataset_id

class _FakeActor:
    def __init__(self, captured, run_result):
        self._captured = captured
        self._run_result = run_result
    def call(self, *, run_input=None):
        self._captured["input"] = run_input
        return self._run_result

class _FakeDataset:
    def iterate_items(self):
        yield {"id": "x"}

class _FakeClient:
    def __init__(self, captured, run_result):
        self._captured = captured
        self._run_result = run_result
    def actor(self, actor_id):
        self._captured["actor"] = actor_id
        return _FakeActor(self._captured, self._run_result)
    def dataset(self, ds_id):
        self._captured["dataset"] = ds_id
        return _FakeDataset()

def test_run_apify_passes_input():
    from mustang_monitor.sources import base
    captured = {}
    client = _FakeClient(captured, _FakeRunResult("ds1"))
    items = list(base.run_apify(client, "acme/actor", {"maxItems": 5}))
    assert captured["actor"] == "acme/actor"
    assert captured["input"] == {"maxItems": 5}
    assert captured["dataset"] == "ds1"
    assert items == [{"id": "x"}]

def test_run_apify_raises_when_run_is_none():
    import pytest
    from mustang_monitor.sources import base
    client = _FakeClient({}, None)
    with pytest.raises(RuntimeError):
        list(base.run_apify(client, "acme/actor", {}))
