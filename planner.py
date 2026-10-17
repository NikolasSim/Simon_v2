import json, os, re, time

class Planner:
    # ступени эскалации: (звук, ожидание ответа в секундах)
    LEVELS = [(None, 15), (1, 20), (2, 25)]

    def __init__(self, voice=None, ask=None, path=None):
        self.path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")
        self.voice = voice
        self.ask = ask or (lambda prompt, timeout: None)
        self.reminders = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def parse_time(self, text, now=None):
        now = now or time.time()
        low = text.lower()
        m = re.search(r"через\s+(\d+)\s*(сек|мин|м\b|час|ч\b)", low)
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            sec = n * 3600 if unit.startswith("ч") else (n if unit.startswith("с") else n * 60)
            return now + sec
        m = re.search(r"(\d{1,2})[:.](\d{2})", text)
        if m:
            hh, mm = int(m.group(1)), int(m.group(2))
            lt = time.localtime(now)
            ts = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, hh, mm, 0, 0, 0, -1))
            if ts <= now + 60:
                ts += 86400
            return ts
        return None

    def add(self, text):
        ts = self.parse_time(text)
        if ts is None:
            return "Не разобрал время, сэр. Скажите, например: напомни 19:00 про таблетки."
        low = text.lower()
        daily = "daily" in low or "каждый день" in low
        body = re.sub(r"напомни\s*(о\s*|про\s*|что\s*)?", "", text, flags=re.IGNORECASE)
        body = re.sub(r"\d{1,2}[:.]\d{2}|через\s+\d+\s*\S+|daily|каждый день", "", body, flags=re.IGNORECASE).strip(" ,.!")
        if not body:
            body = "напоминание"
        self.reminders.append({"text": body, "at": ts, "daily": daily, "answer": None})
        self.save()
        hh = time.strftime("%H:%M", time.localtime(ts))
        return "Записал, сэр: напоминание на " + hh + (" (ежедневно)" if daily else "") + " — " + body + "."

    def list(self):
        if not self.reminders:
            return "Напоминаний нет, сэр."
        out = []
        for r in self.reminders:
            out.append(time.strftime("%d.%m %H:%M", time.localtime(r["at"])) + " — " + r["text"]
                       + (" (ежедневно)" if r.get("daily") else ""))
        return "Ваши напоминания, сэр:\n" + "\n".join(out)

    def due(self):
        now = time.time()
        fired = []
        for r in self.reminders:
            if r["at"] <= now:
                fired.append(r)
                if r.get("daily"):
                    r["at"] += 86400
        self.save()
        return fired

    def _escalate(self, rem):
        for level, (sound, wait) in enumerate(self.LEVELS):
            if sound:
                try:
                    self.voice.alert(sound)
                except Exception:
                    pass
            msg = "Сэр, напоминание: " + rem["text"] + ". Жду вашего ответа."
            if level == 1:
                msg = "Сэр, вы меня слышите? Напоминаю: " + rem["text"] + "."
            if level == 2:
                msg = "Сэр, требуется ваше внимание! Повторяю напоминание: " + rem["text"] + "."
            try:
                self.voice.say(msg)
            except Exception:
                pass
            ans = self.ask("Как ответите, сэр?", wait)
            if ans:
                rem["answer"] = ans
                try:
                    self.voice.say("Принято, сэр. Я записал: " + ans + ".")
                except Exception:
                    pass
                return True
        # финальная ступень: сирена, повтор каждые 60 секунд
        while True:
            try:
                self.voice.alert(3)
                self.voice.say("Сэр, требуется ваше внимание! Напоминание: " + rem["text"] + ".")
            except Exception:
                pass
            ans = self.ask("Как ответите, сэр?", 60)
            if ans:
                rem["answer"] = ans
                return True

    def check_and_notify(self):
        return [self._escalate(r) for r in self.due()]
