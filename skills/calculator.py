import re

def calc(expr):
    expr = expr.replace(",", ".")
    expr = re.sub(r"[^\d\s+\-*/().%]", "", expr)
    if not expr.strip():
        raise ValueError("no expression")
    return eval(expr, {"__builtins__": {}}, {})

def self_test():
    tests = [("2+2", 4), ("3*4", 12), ("(5-1)/2", 2.0)]
    try:
        for e, want in tests:
            if abs(calc(e) - want) > 1e-9:
                return False
        return True
    except Exception:
        return False
