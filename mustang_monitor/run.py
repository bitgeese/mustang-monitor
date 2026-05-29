# mustang_monitor/run.py
from __future__ import annotations
import argparse
import os
from pathlib import Path

from mustang_monitor.models import Listing
from mustang_monitor.spec import load_spec, enabled_sites
from mustang_monitor.filter_rules import passes_hard_filters
from mustang_monitor.vin import vin_disqualifies
from mustang_monitor.state import open_db, classify, mark_seen, cache_vin, get_cached_vin
from mustang_monitor import score_ai, notify

# site name -> module
from mustang_monitor.sources import otomoto, olx, mobilede, autoscout24, willhaben
SITE_MODULES = {"otomoto": otomoto, "olx": olx, "mobilede": mobilede,
                "autoscout24": autoscout24, "willhaben": willhaben}

def process_listing(listing: Listing, spec: dict, conn, vin_decoder, scorer) -> dict:
    """Run one listing through the pipeline. Returns a decision dict (no I/O side effects except state)."""
    ok, reasons = passes_hard_filters(listing, spec)
    if not ok:
        return {"action": "drop", "reasons": reasons}

    if listing.vin:
        decoded = get_cached_vin(conn, listing.vin)
        if decoded is None:
            decoded = vin_decoder(listing.vin)
            if decoded:
                cache_vin(conn, listing.vin, decoded)
        if decoded:
            bad, vreasons = vin_disqualifies(decoded, spec["vin"])
            if bad:
                return {"action": "drop", "reasons": vreasons}

    status = classify(conn, listing.site, listing.listing_id, listing.price_eur)
    if status == "seen":
        return {"action": "skip", "reasons": []}

    score = scorer(listing)
    if score.get("match_score", 0) < spec["scoring"]["min_score_to_alert"]:
        mark_seen(conn, listing.site, listing.listing_id, listing.price_eur,
                  score.get("match_score", 0), notified=False)
        return {"action": "drop", "reasons": [f"score {score.get('match_score')} below threshold"]}

    mark_seen(conn, listing.site, listing.listing_id, listing.price_eur,
              score.get("match_score", 0), notified=True)
    return {"action": "alert", "status": status, "score": score}

def _gather(site: str, spec: dict, apify_client) -> list[Listing]:
    from mustang_monitor.sources.base import run_apify
    cfg = spec["sites"][site]
    mod = SITE_MODULES[site]
    fx = spec["fx"]
    items = run_apify(apify_client, cfg["apify_actor"], cfg["run_input"])
    return [mod.map_item(it, fx) for it in items]

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="config/spec.yaml")
    ap.add_argument("--db", default="state/monitor.db")
    ap.add_argument("--dry-run", action="store_true", help="print would-be alerts, do not send or persist")
    ap.add_argument("--backfill-silent", action="store_true", help="seed state without alerting")
    args = ap.parse_args(argv)

    spec = load_spec(Path(args.spec))
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = open_db(args.db)

    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    from apify_client import ApifyClient
    apify_client = ApifyClient(os.environ.get("APIFY_TOKEN", ""))

    ai_client = score_ai.get_client()
    scorer = lambda l: score_ai.score_listing(l, ai_client)
    from mustang_monitor.vin import decode_vin

    first_run = conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0] == 0
    cap = spec["notify"]["first_run_digest_cap"]
    alerts: list[tuple[Listing, dict, str]] = []

    for site in enabled_sites(spec):
        try:
            listings = _gather(site, spec, apify_client)
        except Exception as e:  # isolate per-site failure
            if not args.dry_run and token:
                notify.send_text(f"⚠️ {site} fetch failed: {e}", token, chat_id)
            continue
        for listing in listings:
            decision = process_listing(listing, spec, conn, vin_decoder=decode_vin, scorer=scorer)
            if decision["action"] == "alert" and not args.backfill_silent:
                alerts.append((listing, decision["score"], decision["status"]))

    if args.dry_run:
        for listing, score, status in alerts:
            print(notify.format_message(listing, score, status))
        return 0

    to_send = alerts[:cap] if first_run else alerts
    for listing, score, status in to_send:
        if token:
            notify.send_match(listing, score, status, token, chat_id)
    if first_run and len(alerts) > cap and token:
        notify.send_text(f"…and {len(alerts) - cap} more current matches (capped first-run digest).", token, chat_id)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
