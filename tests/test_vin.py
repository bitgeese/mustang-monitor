import responses
from mustang_monitor.vin import extract_vin, decode_vin, vin_disqualifies

SPEC_VIN = {
    "require_engine_cylinders": 8,
    "reject_displacement_below": 4.0,
    "reject_body_contains": ["convertible", "cabriolet"],
    "reject_trim_contains": ["cobra", "svt"],
}

def test_extract_vin_found():
    assert extract_vin("VIN: 1FAFP42X11F123456 clean") == "1FAFP42X11F123456"

def test_extract_vin_none():
    assert extract_vin("no vin here") is None

@responses.activate
def test_decode_vin_calls_vpic():
    responses.add(
        responses.GET,
        "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/1FAFP42X11F123456",
        json={"Results": [{"ModelYear": "2001", "BodyClass": "Coupe", "EngineCylinders": "8",
                            "DisplacementL": "4.6", "Trim": "GT", "Make": "FORD", "Model": "Mustang"}]},
        status=200,
    )
    decoded = decode_vin("1FAFP42X11F123456")
    assert decoded["Trim"] == "GT"
    assert decoded["DisplacementL"] == "4.6"

def test_disqualify_v6():
    decoded = {"EngineCylinders": "6", "DisplacementL": "3.8", "BodyClass": "Coupe", "Trim": "Base"}
    bad, reasons = vin_disqualifies(decoded, SPEC_VIN)
    assert bad and any("cylinders" in r or "displacement" in r for r in reasons)

def test_disqualify_cobra():
    decoded = {"EngineCylinders": "8", "DisplacementL": "4.6", "BodyClass": "Coupe", "Trim": "SVT Cobra"}
    bad, reasons = vin_disqualifies(decoded, SPEC_VIN)
    assert bad and any("trim" in r for r in reasons)

def test_disqualify_convertible():
    decoded = {"EngineCylinders": "8", "DisplacementL": "4.6", "BodyClass": "Convertible", "Trim": "GT"}
    bad, reasons = vin_disqualifies(decoded, SPEC_VIN)
    assert bad and any("body" in r for r in reasons)

def test_gt_passes():
    decoded = {"EngineCylinders": "8", "DisplacementL": "4.6", "BodyClass": "Coupe", "Trim": "GT"}
    bad, reasons = vin_disqualifies(decoded, SPEC_VIN)
    assert not bad and reasons == []

def test_unknown_or_empty_fields_pass_through():
    # junk/unknown VIN -> vPIC returns empty fields -> must NOT disqualify (pipeline relies on this)
    assert vin_disqualifies({}, SPEC_VIN) == (False, [])
    assert vin_disqualifies({"EngineCylinders": "", "DisplacementL": "", "BodyClass": "", "Trim": ""}, SPEC_VIN) == (False, [])
