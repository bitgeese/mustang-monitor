# tests/test_run.py
from mustang_monitor.models import Listing
from mustang_monitor.run import process_listing
from mustang_monitor.state import open_db

SPEC = {
    "years": {"min": 1999, "max": 2004},
    "price_eur": {"min": 4000, "max": 26000},
    "mileage_km": {"min": 0, "max": 220000},
    "keywords": {"convertible": ["cabrio"], "automatic": ["automat"], "salvage": ["powypadkowy"]},
    "vin": {"require_engine_cylinders": 8, "reject_displacement_below": 4.0,
            "reject_body_contains": ["convertible"], "reject_trim_contains": ["cobra"]},
    "scoring": {"min_score_to_alert": 60},
}

def _mk(**kw):
    base = dict(site="s", listing_id="1", url="u", title="Ford Mustang GT 2001", price_eur=8000.0,
                currency="EUR", mileage_km=120000, year=2001, location="x", description="manual coupe")
    base.update(kw)
    return Listing(**base)

def test_process_rejected_by_rules(tmp_path):
    conn = open_db(tmp_path / "m.db")
    decision = process_listing(_mk(title="Mustang GT Cabrio"), SPEC, conn,
                               vin_decoder=lambda v: {}, scorer=lambda l: {"match_score": 90, "ai_unscored": False})
    assert decision["action"] == "drop"
    assert "convertible" in " ".join(decision["reasons"])

def test_process_below_score_threshold(tmp_path):
    conn = open_db(tmp_path / "m.db")
    decision = process_listing(_mk(vin=None), SPEC, conn,
                               vin_decoder=lambda v: {},
                               scorer=lambda l: {"match_score": 40, "ai_unscored": False, "red_flags": []})
    assert decision["action"] == "drop"
    assert "score" in " ".join(decision["reasons"])

def test_process_new_match_alerts(tmp_path):
    conn = open_db(tmp_path / "m.db")
    decision = process_listing(_mk(), SPEC, conn,
                               vin_decoder=lambda v: {},
                               scorer=lambda l: {"match_score": 80, "ai_unscored": False, "red_flags": []})
    assert decision["action"] == "alert"
    assert decision["status"] == "new"

def test_process_seen_is_skipped_second_time(tmp_path):
    conn = open_db(tmp_path / "m.db")
    scorer = lambda l: {"match_score": 80, "ai_unscored": False, "red_flags": []}
    first = process_listing(_mk(), SPEC, conn, vin_decoder=lambda v: {}, scorer=scorer)
    assert first["action"] == "alert"
    decision = process_listing(_mk(), SPEC, conn, vin_decoder=lambda v: {}, scorer=scorer)
    assert decision["action"] == "skip"

def test_process_vin_disqualifies(tmp_path):
    conn = open_db(tmp_path / "m.db")
    decision = process_listing(_mk(vin="1FAFP42X11F123456"), SPEC, conn,
                               vin_decoder=lambda v: {"EngineCylinders": "6", "DisplacementL": "3.8"},
                               scorer=lambda l: {"match_score": 90, "ai_unscored": False})
    assert decision["action"] == "drop"
    assert any("displacement" in r or "cylinders" in r for r in decision["reasons"])

def test_main_dry_run_prints_and_does_not_persist(tmp_path, monkeypatch, capsys):
    from pathlib import Path
    from mustang_monitor import run as run_mod
    # Avoid network/AI: stub the per-site fetch and the scorer; restrict to one site.
    monkeypatch.setattr(run_mod, "enabled_sites", lambda spec: ["otomoto"])
    monkeypatch.setattr(run_mod, "_gather", lambda site, spec, client: [_mk()])
    monkeypatch.setattr(run_mod.score_ai, "score_listing",
                        lambda l, client: {"match_score": 90, "ai_unscored": False,
                                           "red_flags": [], "recommendation": "strong"})
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    spec_path = Path(__file__).parent.parent / "config" / "spec.yaml"
    real_db = tmp_path / "real.db"
    rc = run_mod.main(["--dry-run", "--spec", str(spec_path), "--db", str(real_db)])
    assert rc == 0
    assert not real_db.exists()  # dry-run must NOT create/persist the real db
    assert "Mustang" in capsys.readouterr().out  # printed a would-be alert
