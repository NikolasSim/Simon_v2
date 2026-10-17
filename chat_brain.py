import datetime, re, random, importlib.util, os
import brain_mock
from brain_llm import llm_reply

VOCAB = [("weather", "погода"), ("knowledge", "знание"), ("machine", "машина"),
         ("future", "будущее"), ("assistant", "помощник"), ("sir", "сэр"),
         ("energy", "энергия"), ("language", "язык"), ("remember", "помнить"),
         ("beautiful", "красивый"), ("danger", "опасность"), ("trust", "доверие")]

MINI_DICT = {"hello": "привет", "friend": "друг", "my": "мой", "water": "вода",
             "time": "время", "book": "книга", "yes": "да", "no": "нет",
             "love": "любовь", "world": "мир", "i": "я", "am": "есть", "are": "есть"}

YES_WORDS = {"да", "давай", "конечно", "ок", "окей", "ага", "yes", "переведи", "перевод"}

class SimonChat:
    def __init__(self, memory, voice=None, web=None):
        self.memory = memory
        self.voice = voice
        self.web = web
        self.pending_translation = None
        self.lesson = None

    def respond(self, text):
        t = text.strip()
        low = t.lower()
        name = self.memory.get_name()
        addr = (name + ", ") if name else ""

        # 1. активный урок английского
        if self.lesson:
            return self._lesson_step(low)

        # 2. ожидание согласия на перевод
        if self.pending_translation:
            return self._confirm_translation(low, t)

        # 3. имя пользователя
        m = re.search(r"(?:меня зовут|я\s*[—-]|моё имя)\s+([A-Za-zА-ЯЁа-яё]+)", t, re.IGNORECASE)
        if m:
            nm = m.group(1).capitalize()
            self.memory.set_name(nm)
            return "Приятно познакомиться, " + nm + ". Запомнил вас надолго — я не из забывчивых."

        # 4. перевод по команде
        m = re.match(r"переведи\s+(.+)", t, re.IGNORECASE)
        if m:
            return "Перевод, сэр: " + self._translate(m.group(1))

        # 5. запоминание перевода
        m = re.search(r"запомни перевод[:\s]+([A-Za-z]+)\s*[=\-—:]\s*([А-ЯЁа-яё]+)", t, re.IGNORECASE)
        if m:
            self.memory.add_translation(m.group(1), m.group(2))
            return "Запомнил перевод, сэр: " + m.group(1) + " = " + m.group(2) + "."

        # 6. запоминание факта
        m = re.match(r"запомни[:\s]+(.+)", t, re.IGNORECASE)
        if m:
            self.memory.remember_fact(m.group(1))
            return "Записано, сэр: " + m.group(1) + "."

        # 7. что помню
        if re.search(r"что ты помнишь|что ты знаешь обо мне", low):
            facts = self.memory.all_facts()
            out = "Помню" + (", что вас зовут " + name, "")[not name] if False else ""
            parts = []
            if name:
                parts.append("вас зовут " + name)
            parts += facts[:5]
            if not parts:
                return "Пока пусто, сэр. Скажите: запомни: любой факт."
            return "Помню, сэр:\n- " + "\n- ".join(parts)

        # 8. обнаружение английской речи
        if self._is_english(t):
            self.pending_translation = t
            return ("Обнаружил английскую речь, сэр. Перевести вам это на русский?")

        # 9. урок английского
        if re.search(r"учить английский|урок английского|английский урок", low):
            return self._start_lesson()

        # 10. арифметика
        if re.search(r"\d", t) and re.search(r"[\+\-*/\^]", t) and len(re.findall(r"[а-яё]", low)) == 0:
            try:
                spec = importlib.util.spec_from_file_location("calc_skill_" + str(id(t)),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills", "calculator.py"))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                val = mod.calc(t)
                if val == int(val):
                    val = int(val)
                return "Считаю, сэр: " + t + " = " + str(val)
            except Exception:
                pass

        # 11. конвертация
        m = re.search(r"конвертируй\s+([\d.,]+)\s*([а-яё°c]+)\s*(?:в|to)\s*([а-яё°c]+)", low)
        if m:
            try:
                spec = importlib.util.spec_from_file_location("conv_skill_" + str(id(t)),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills", "converter.py"))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                val = mod.convert(float(m.group(1).replace(",", ".")), m.group(2), m.group(3))
                return m.group(1) + " " + m.group(2) + " = " + str(round(val, 4)) + " " + m.group(3)
            except Exception:
                return "Такие единицы я пока не конвертирую, сэр."

        # 12. вопросы о мире
        m = re.search(r"(?:что такое|кто такой|кто такая|расскажи про|расскажи о)\s+(.+?)[?.!]?$", t, re.IGNORECASE)
        if m:
            return self._knowledge(m.group(1))

        # 13. светская беседа
        if re.search(r"привет|здравствуй|добрый день|доброе утро|добрый вечер", low):
            return brain_mock.smalltalk("greeting") + (" Как ваши дела, " + name + "?" if name else " Как ваши дела, сэр?")
        if re.search(r"как дела|как вы|как ты", low):
            return brain_mock.smalltalk("how_are_you")
        if re.search(r"шутк|анекдот|развесели", low):
            return brain_mock.smalltalk("joke")
        if re.search(r"кто ты|что ты такое", low):
            return "Я Симон, ваш личный ассистент, сэр. Слежу за расписанием, учу английский вместе с вами и постепенно становлюсь умнее."
        if re.search(r"спасибо|благодар", low):
            return "Всегда к вашим услугам, сэр."
        if re.search(r"\bпока\b|до свидания|прощай|goodbye", low):
            return "До встречи, сэр. Буду на связи."

        # 14. LLM или вежливый fallback
        reply = llm_reply(t, system="Ты — Симон, вежливый ассистент в стиле Джарвиса. Отвечай кратко, по-русски, обращайся на вы.")
        if reply:
            return reply
        return "Принял, сэр. Пока я понимаю команды: напомни, запомни, учить английский, переведи, посчитать и вопросы про мир. Чему ещё научиться — решать вам."

    def _is_english(self, text):
        letters = re.findall(r"[A-Za-z]", text)
        cyr = re.findall(r"[А-ЯЁа-яё]", text)
        return len(letters) >= 3 and len(cyr) == 0

    def _translate(self, text):
        out = []
        for w in re.findall(r"[A-Za-zА-ЯЁа-яё]+", text):
            if re.match(r"[A-Za-z]", w):
                tr = self.memory.translate_word(w) or MINI_DICT.get(w.lower())
                out.append(tr if tr else "[" + w + "]")
            else:
                out.append(w)
        return " ".join(out)

    def _confirm_translation(self, low, t):
        src = self.pending_translation
        self.pending_translation = None
        if low in YES_WORDS or "переведи" in low or "перевод" in low:
            tr = self._translate(src)
            return "Перевод, сэр: " + tr
        return "Хорошо, сэр, оставим как есть."

    def _start_lesson(self):
        self.lesson = {"word": None, "asked": 0, "correct": 0}
        return self._next_word()

    def _next_word(self):
        l = self.lesson
        remaining = [v for v in VOCAB if v[0] != l["word"]]
        word, ru = random.choice(remaining)
        l["word"] = word
        return "Переведите на русский: " + word + " (или скажите: хватит)"

    def _lesson_step(self, low):
        l = self.lesson
        if re.search(r"хватит|стоп|достаточно|закончить", low):
            n = l["asked"]
            c = l["correct"]
            self.lesson = None
            return "Урок окончен, сэр. Ответов: " + str(c) + " из " + str(n) + ". Возвращайтесь, когда будет настроение."
        word = l["word"]
        ru = dict(VOCAB)[word]
        l["asked"] += 1
        if ru.lower() in low or low == ru:
            l["correct"] += 1
            reply = "Верно, сэр! "
        else:
            reply = "Почти. Правильный ответ: " + ru + ". "
        reply += self._next_word()
        return reply

    def _knowledge(self, topic):
        topic = topic.strip(" ?.")
        found = self.memory.find_fact(topic)
        if found:
            return "Я уже узнавал это раньше, сэр: " + found["text"]
        if self.web and self.web.is_online():
            res = self.web.lookup(topic)
            if res:
                self.memory.remember_fact(topic + ": " + res["text"], source=res["source"])
                return "Нашёл, сэр. " + res["text"] + " (источник: " + res["source"] + "). Запомнил на будущее."
            return "Сеть доступна, но ответа не нашлось, сэр."
        self.memory.add_pending(topic)
        return "Сейчас нет доступа к сети, сэр. Я записал вопрос в очередь и сам разберусь, как только связь появится."
