from __future__ import annotations
import re
import requests

# 17 chars, no I/O/Q
_VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
_VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"

def extract_vin(text: str | None) -> str | None:
    if not text:
        return None
    m = _VIN_RE.search(text.upper())
    return m.group(1) if m else None

def decode_vin(vin: str, timeout: float = 10.0) -> dict:
    # NOTE: vPIC returns HTTP 200 even for junk VINs (Results[0]["ErrorCode"] != "0"),
    # leaving the engine/body fields empty. vin_disqualifies then fires nothing and the
    # listing flows on to the AI scorer — conservatively safe (never a false reject).
    resp = requests.get(_VPIC.format(vin=vin), timeout=timeout)
    resp.raise_for_status()
    results = resp.json().get("Results") or [{}]
    return results[0]

def _to_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def vin_disqualifies(decoded: dict, spec_vin: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    cyl = decoded.get("EngineCylinders")
    if cyl not in (None, "") and str(cyl) != str(spec_vin["require_engine_cylinders"]):
        reasons.append(f"cylinders {cyl} != {spec_vin['require_engine_cylinders']}")
    disp = _to_float(decoded.get("DisplacementL"))
    if disp is not None and disp < spec_vin["reject_displacement_below"]:
        reasons.append(f"displacement {disp} below {spec_vin['reject_displacement_below']}")
    body = (decoded.get("BodyClass") or "").lower()
    for bad in spec_vin["reject_body_contains"]:
        if bad in body:
            reasons.append(f"body contains {bad}")
    trim = (decoded.get("Trim") or "").lower()
    for bad in spec_vin["reject_trim_contains"]:
        if bad in trim:
            reasons.append(f"trim contains {bad}")
    return (len(reasons) > 0, reasons)
