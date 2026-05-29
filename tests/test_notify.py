# tests/test_notify.py
import responses
from mustang_monitor.models import Listing
from mustang_monitor.notify import format_message, send_match

def _mk():
    return Listing(site="otomoto", listing_id="1", url="http://otomoto/1", title="Ford Mustang GT 2001",
                   price_eur=8000.0, currency="EUR", mileage_km=120000, year=2001,
                   location="Warszawa", description="manual", photos=["http://img/1.jpg"])

def test_format_message_contains_key_facts():
    score = {"match_score": 80, "red_flags": ["light rust"], "recommendation": "inspect", "ai_unscored": False}
    text = format_message(_mk(), score, status="new")
    assert "Mustang GT" in text
    assert "8000" in text
    assert "120000" in text or "120,000" in text
    assert "http://otomoto/1" in text
    assert "80" in text

@responses.activate
def test_send_match_posts_to_telegram():
    responses.add(responses.POST, "https://api.telegram.org/botTOKEN/sendMessage",
                  json={"ok": True}, status=200)
    score = {"match_score": 80, "red_flags": [], "recommendation": "inspect", "ai_unscored": False}
    send_match(_mk(), score, status="new", token="TOKEN", chat_id="42")
    assert len(responses.calls) == 1
    assert "chat_id=42" in responses.calls[0].request.body or "42" in responses.calls[0].request.body
