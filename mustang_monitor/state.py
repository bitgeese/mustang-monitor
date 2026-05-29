from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path

_PRICE_DROP_FRACTION = 0.05  # >=5% drop re-alerts

def open_db(path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen (
            site TEXT, listing_id TEXT, first_seen REAL, last_seen REAL,
            price_eur REAL, score INTEGER, notified INTEGER,
            PRIMARY KEY (site, listing_id)
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vin_cache (
            vin TEXT PRIMARY KEY, decoded_json TEXT, fetched_at REAL
        )""")
    conn.commit()
    return conn

def classify(conn: sqlite3.Connection, site: str, listing_id: str, price_eur: float | None) -> str:
    row = conn.execute(
        "SELECT price_eur FROM seen WHERE site=? AND listing_id=?", (site, listing_id)
    ).fetchone()
    if row is None:
        return "new"
    old_price = row[0]
    if price_eur is not None and old_price is not None and old_price > 0:
        if price_eur <= old_price * (1 - _PRICE_DROP_FRACTION):
            return "price_drop"
    return "seen"

def mark_seen(conn, site, listing_id, price_eur, score, notified):
    now = time.time()
    conn.execute("""
        INSERT INTO seen (site, listing_id, first_seen, last_seen, price_eur, score, notified)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(site, listing_id) DO UPDATE SET
            last_seen=excluded.last_seen, price_eur=excluded.price_eur,
            score=excluded.score, notified=seen.notified OR excluded.notified
    """, (site, listing_id, now, now, price_eur, score, int(notified)))
    conn.commit()

def cache_vin(conn, vin: str, decoded: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO vin_cache (vin, decoded_json, fetched_at) VALUES (?,?,?)",
        (vin, json.dumps(decoded), time.time()),
    )
    conn.commit()

def get_cached_vin(conn, vin: str) -> dict | None:
    row = conn.execute("SELECT decoded_json FROM vin_cache WHERE vin=?", (vin,)).fetchone()
    return json.loads(row[0]) if row else None
