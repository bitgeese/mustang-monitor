# tests/test_score_ai.py
from mustang_monitor.models import Listing
from mustang_monitor.score_ai import score_listing, _build_prompt

def _mk():
    return Listing(site="s", listing_id="1", url="u", title="Ford Mustang GT 2001",
                   price_eur=8000.0, currency="EUR", mileage_km=120000, year=2001,
                   location="x", description="5-bieg manual, lekka korozja progów",
                   photos=["http://img/1.jpg"])

def test_build_prompt_includes_spec_and_text():
    prompt = _build_prompt(_mk())
    assert "Mustang" in prompt
    assert "manual" in prompt.lower()
    assert "JSON" in prompt

def test_score_listing_degrades_without_client():
    # No client -> rules-only neutral score, flagged unscored
    result = score_listing(_mk(), client=None)
    assert result["ai_unscored"] is True
    assert result["match_score"] == 50

def test_score_listing_parses_model_json():
    class FakeBlock:
        text = '{"transmission":"manual","trim_confirm":"GT","red_flags":["light rust"],"rust_risk":"medium","condition_notes":"ok","match_score":78,"recommendation":"inspect"}'
    class FakeMsg:
        content = [FakeBlock()]
    class FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return FakeMsg()
    result = score_listing(_mk(), client=FakeClient())
    assert result["match_score"] == 78
    assert result["transmission"] == "manual"
    assert result["ai_unscored"] is False

def test_score_listing_strips_uppercase_json_fence():
    class FakeBlock:
        text = '```JSON\n{"match_score": 81, "red_flags": []}\n```'
    class FakeMsg:
        content = [FakeBlock()]
    class FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                return FakeMsg()
    result = score_listing(_mk(), client=FakeClient())
    assert result["match_score"] == 81
    assert result["ai_unscored"] is False

def test_score_listing_degrades_on_api_exception():
    class FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("api down")
    result = score_listing(_mk(), client=FakeClient())
    assert result["ai_unscored"] is True
    assert result["match_score"] == 50
