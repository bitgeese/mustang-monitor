# mustang_monitor/notify.py
from __future__ import annotations
import requests
from mustang_monitor.models import Listing

def format_message(listing: Listing, score: dict, status: str) -> str:
    flags = ", ".join(score.get("red_flags") or []) or "none"
    ai_note = " (AI-unscored)" if score.get("ai_unscored") else ""
    tag = {"new": "🆕 NEW MATCH", "price_drop": "💸 PRICE DROP"}.get(status, status.upper())
    return (
        f"{tag} — {listing.site}\n"
        f"{listing.title}\n"
        f"€{listing.price_eur} · {listing.mileage_km} km · {listing.year} · {listing.location}\n"
        f"score {score.get('match_score')}{ai_note} · {score.get('recommendation')}\n"
        f"red flags: {flags}\n"
        f"{listing.url}"
    )

def send_match(listing: Listing, score: dict, status: str, token: str, chat_id: str,
               timeout: float = 10.0) -> None:
    text = format_message(listing, score, status)
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text, "disable_web_page_preview": False},
        timeout=timeout,
    )
    resp.raise_for_status()

def send_text(text: str, token: str, chat_id: str, timeout: float = 10.0) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}, timeout=timeout,
    )
    resp.raise_for_status()
