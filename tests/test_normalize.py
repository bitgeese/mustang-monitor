from mustang_monitor.normalize import parse_price_eur, parse_mileage_km, parse_year

def test_parse_price_eur_from_pln():
    assert parse_price_eur("39 900 zł", {"PLN": 0.23, "EUR": 1.0}) == round(39900 * 0.23, 2)

def test_parse_price_eur_from_eur():
    assert parse_price_eur("€8.500", {"PLN": 0.23, "EUR": 1.0}) == 8500.0

def test_parse_price_eur_unparseable():
    assert parse_price_eur("ask", {"EUR": 1.0}) is None

def test_parse_mileage_variants():
    assert parse_mileage_km("123 456 km") == 123456
    assert parse_mileage_km("120.000 km") == 120000
    assert parse_mileage_km("98 tys. km") == 98000
    assert parse_mileage_km("brak") is None

def test_parse_year():
    assert parse_year("Ford Mustang GT 2001") == 2001
    assert parse_year("rok 1999") == 1999
    assert parse_year("no digits here") is None
