import json, os, time, re

class Memory:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
        self.data = {"facts": [], "name": None, "translations": {},
                     "history": [], "pending": [], "profile": {}}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except Exception:
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def set_name(self, name):
        self.data["name"] = name
        self.save()

    def get_name(self):
        return self.data.get("name")

    def remember_fact(self, text, source=None):
        text = text.strip()
        for f in self.data["facts"]:
            if f["text"].lower() == text.lower():
                return False
        self.data["facts"].append({"text": text, "source": source, "ts": time.time()})
        self.save()
        return True

    def find_fact(self, query):
        q = query.lower()
        words = [w for w in re.findall(r"[a-zа-яё0-9]+", q) if len(w) > 2]
        best, score = None, 0
        for f in self.data["facts"]:
            t = f["text"].lower()
            s = sum(1 for w in words if w in t)
            if s > score:
                best, score = f, s
        return best if score >= 1 else None

    def all_facts(self):
        return [f["text"] for f in self.data["facts"]]

    def add_translation(self, en, ru):
        self.data["translations"][en.lower()] = ru
        self.save()

    def translate_word(self, en):
        return self.data["translations"].get(en.lower())

    def add_dialog(self, role, text):
        self.data["history"].append({"role": role, "text": text, "ts": time.time()})
        self.data["history"] = self.data["history"][-200:]
        self.save()

    def add_pending(self, question):
        q = question.strip()
        if q and q not in [p["q"] for p in self.data["pending"]]:
            self.data["pending"].append({"q": q, "ts": time.time()})
            self.save()

    def take_pending(self):
        if self.data["pending"]:
            return self.data["pending"].pop(0)["q"]
        return None
