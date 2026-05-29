# mustang_monitor/score_ai.py
from __future__ import annotations
import json
import os
from mustang_monitor.models import Listing

MODEL = "claude-haiku-4-5-20251001"

_RED_FLAGS = ("rust on rear frame rails/subframe, timing-chain rattle, cracked plastic intake / "
              "coolant loss, lowered or heavily modified suspension, flood damage, VIN tampering")

def _build_prompt(listing: Listing) -> str:
    return (
        "You are vetting a used 1999-2004 Ford Mustang GT (manual, coupe) for an overland build.\n"
        "From the listing text (Polish/German/English) and photos, return ONLY JSON with keys: "
        "transmission ('manual'|'automatic'|'unknown'), trim_confirm, red_flags (array), "
        "rust_risk ('low'|'medium'|'high'|'unknown'), condition_notes, match_score (0-100 int), "
        "recommendation ('strong'|'inspect'|'skip').\n"
        f"Known red flags to look for: {_RED_FLAGS}.\n"
        "Photo-based rust is a 'go inspect' hint, never a hard reject.\n\n"
        f"TITLE: {listing.title}\nPRICE_EUR: {listing.price_eur}\nMILEAGE_KM: {listing.mileage_km}\n"
        f"YEAR: {listing.year}\nLOCATION: {listing.location}\nDESCRIPTION:\n{listing.description}\n"
    )

def get_client():
    """Return an Anthropic client, or None if no API key is configured."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=key)

def _rules_only() -> dict:
    return {"transmission": None, "trim_confirm": None, "red_flags": [], "rust_risk": "unknown",
            "condition_notes": "", "match_score": 50, "recommendation": "inspect", "ai_unscored": True}

def score_listing(listing: Listing, client) -> dict:
    if client is None:
        return _rules_only()
    content = [{"type": "text", "text": _build_prompt(listing)}]
    for url in listing.photos[:3]:
        content.append({"type": "image", "source": {"type": "url", "url": url}})
    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=400,
            messages=[{"role": "user", "content": content}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        data = json.loads(raw)
        data["ai_unscored"] = False
        return data
    except Exception:
        return _rules_only()
