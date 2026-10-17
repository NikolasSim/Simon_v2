PAIRS = {
    ("км", "мили"): 0.621371,
    ("мили", "км"): 1.609344,
    ("кг", "фунты"): 2.20462,
    ("фунты", "кг"): 0.453592,
    ("м", "футы"): 3.28084,
    ("футы", "м"): 0.3048,
    ("л", "галлоны"): 0.264172,
    ("галлоны", "л"): 3.78541,
}

def convert(value, unit_from, unit_to):
    if unit_from in ("цельсия", "ц", "c") and unit_to in ("фаренгейта", "ф", "f"):
        return value * 9 / 5 + 32
    if unit_from in ("фаренгейта", "ф", "f") and unit_to in ("цельсия", "ц", "c"):
        return (value - 32) * 5 / 9
    f = PAIRS.get((unit_from, unit_to))
    if f is None:
        raise ValueError("unknown units")
    return value * f

def self_test():
    tests = [
        (10, "км", "мили", 6.21371),
        (100, "ц", "f", 212.0),
        (1, "кг", "фунты", 2.20462),
    ]
    try:
        for v, u1, u2, want in tests:
            if abs(convert(v, u1, u2) - want) > 1e-3:
                return False
        return True
    except Exception:
        return False

if __name__ == "__main__":
    print("self_test:", self_test())
