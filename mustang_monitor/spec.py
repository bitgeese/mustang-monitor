from __future__ import annotations
from pathlib import Path
import yaml

def load_spec(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def enabled_sites(spec: dict) -> list[str]:
    return [name for name, cfg in spec["sites"].items() if cfg.get("enabled")]
