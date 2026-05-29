from pathlib import Path
from mustang_monitor.spec import load_spec

def test_load_spec_reads_yaml():
    spec = load_spec(Path(__file__).parent.parent / "config/spec.yaml")
    assert spec["years"]["min"] == 1999
    assert spec["years"]["max"] == 2004
    assert spec["scoring"]["min_score_to_alert"] == 60
    assert "otomoto" in spec["sites"]

def test_enabled_sites_helper():
    from mustang_monitor.spec import enabled_sites
    spec = {"sites": {"a": {"enabled": True}, "b": {"enabled": False}}}
    assert enabled_sites(spec) == ["a"]
