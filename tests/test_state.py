from mustang_monitor.state import open_db, classify, mark_seen, cache_vin, get_cached_vin

def test_new_then_seen(tmp_path):
    conn = open_db(tmp_path / "m.db")
    assert classify(conn, "otomoto", "1", price_eur=8000.0) == "new"
    mark_seen(conn, "otomoto", "1", price_eur=8000.0, score=80, notified=True)
    assert classify(conn, "otomoto", "1", price_eur=8000.0) == "seen"

def test_price_drop_detected(tmp_path):
    conn = open_db(tmp_path / "m.db")
    mark_seen(conn, "olx", "2", price_eur=10000.0, score=70, notified=True)
    assert classify(conn, "olx", "2", price_eur=8000.0) == "price_drop"
    assert classify(conn, "olx", "2", price_eur=9999.0) == "seen"  # <5% drop ignored

def test_vin_cache_roundtrip(tmp_path):
    conn = open_db(tmp_path / "m.db")
    assert get_cached_vin(conn, "VIN1") is None
    cache_vin(conn, "VIN1", {"Trim": "GT"})
    assert get_cached_vin(conn, "VIN1") == {"Trim": "GT"}
