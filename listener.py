import re

WAKE = re.compile(r"\bсимон(?:а|е|ом)?\b|\bsimon\b", re.IGNORECASE)

def has_wake(text):
    m = WAKE.search(text)
    if not m:
        return False
    before_words = text[:m.start()].lower().split()
    if before_words and before_words[-1] in ("без", "не", "кроме"):
        return False
    return True

def strip_wake(text):
    return WAKE.sub("", text).strip(" ,.!?:;-")
