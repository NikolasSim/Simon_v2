import json, os, re, time, threading, importlib.util, py_compile
import memory as memory_mod
import voice as voice_mod
import listener
import web_knowledge
from chat_brain import SimonChat
from planner import Planner

BASE = os.path.dirname(os.path.abspath(__file__))

class SimonAgent:
    def __init__(self, use_voice=True, planner=True):
        self.memory = memory_mod.Memory()
        self.voice = voice_mod.Voice() if use_voice else None
        self.chat = SimonChat(self.memory, self.voice, web=web_knowledge)
        self.planner = Planner(voice=self.voice, ask=self._ask_user) if planner else None
        self.online = web_knowledge.is_online()
        self.last_replacement = os.path.join(BASE, "last_replacement.json")
        if self.online:
            learned = web_knowledge.learn_pending(self.memory)
        wake_env = os.environ.get("JARVIS_WAKE", "")
        self.wake_mode = wake_env == "1"
        if self.planner and self.voice and self.voice.backend == "android":
            threading.Thread(target=self._planner_loop, daemon=True).start()

    def _planner_loop(self):
        while True:
            try:
                self.planner.check_and_notify()
            except Exception:
                pass
            time.sleep(5)

    def _ask_user(self, prompt, timeout):
        if self.voice:
            return self.voice.listen(prompt, timeout)
        return None

    def handle(self, text):
        text = text.strip()
        if not text:
            return None
        if self.wake_mode and not listener.has_wake(text):
            return None
        if listener.has_wake(text):
            text = listener.strip_wake(text)
        if not text:
            return None
        low = text.lower()

        # откат последней замены
        if "откатись" in low:
            return self.rollback()

        # напоминания
        if re.match(r"напомни\b", low) and self.planner:
            return self.planner.add(text)
        if re.search(r"покажи напоминания|какие напоминания|мои напоминания", low) and self.planner:
            return self.planner.list()

        # подтверждение улучшения
        if low in ("да", "yes", "подтверждаю", "давай") and self._pending_proposal():
            return self._apply_proposal(self._pending_proposal())
        if low in ("нет", "no", "откажись", "не надо") and self._pending_proposal():
            self._save_proposal(self._pending_proposal(), approved=False)
            self._clear_proposal()
            return "Принято, сэр. Предложение сохранено — вернусь к нему позже."

        reply = self.chat.respond(text)
        self.memory.add_dialog("user", text)
        if reply:
            self.memory.add_dialog("simon", reply)
        return reply

    # --- самоулучшение навыков ---

    def propose_improvement(self, skill="calculator"):
        path = os.path.join(BASE, "skills", skill + ".py")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        new_src = src
        if skill == "calculator" and ".replace(\"^\", \"**\")" not in src:
            new_src = src.replace('expr = expr.replace(",", ".")',
                                  'expr = expr.replace("^", "**").replace(",", ".")')
        if new_src == src:
            return None
        ok, report = self._check_new_version(new_src, skill)
        if not ok:
            return None
        proposal = {"skill": skill, "reason": "добавление поддержки степеней",
                    "new_src": new_src, "test_report": report}
        self._save_proposal(proposal)
        return proposal

    def _check_new_version(self, new_src, skill):
        if "def self_test" not in new_src:
            return False, "нет обязательного самотеста"
        try:
            compile(new_src, skill + "_new.py", "exec")
        except Exception as e:
            return False, "не компилируется: " + str(e)
        tmp = os.path.join(BASE, "_tmp_check_" + str(int(time.time() * 1000)) + ".py")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(new_src)
            spec = importlib.util.spec_from_file_location("check_" + str(int(time.time() * 1000)), tmp)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not mod.self_test():
                return False, "самотест новой версии провален"
        except Exception as e:
            return False, "ошибка при прогоне самотеста: " + str(e)
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass
        return True, "все проверки пройдены"

    def _proposal_path(self):
        return os.path.join(BASE, "pending_proposals.json")

    def _save_proposal(self, proposal, approved=None):
        data = dict(proposal)
        if approved is not None:
            data["approved"] = approved
        with open(self._proposal_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _pending_proposal(self):
        try:
            with open(self._proposal_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _clear_proposal(self):
        try:
            os.remove(self._proposal_path())
        except Exception:
            pass

    def _apply_proposal(self, proposal):
        skill = proposal["skill"]
        path = os.path.join(BASE, "skills", skill + ".py")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BASE, "backups", skill + "_" + stamp + ".py")
        with open(path, "r", encoding="utf-8") as f:
            old = f.read()
        with open(backup, "w", encoding="utf-8") as f:
            f.write(old)
        with open(path, "w", encoding="utf-8") as f:
            f.write(proposal["new_src"])
        with open(self.last_replacement, "w", encoding="utf-8") as f:
            json.dump({"skill": skill, "backup": backup}, f)
        self._clear_proposal()
        return "Готово, сэр: навык " + skill + " обновлён. Прежняя версия сохранена в backups."

    def rollback(self):
        try:
            with open(self.last_replacement, "r", encoding="utf-8") as f:
                info = json.load(f)
            path = os.path.join(BASE, "skills", info["skill"] + ".py")
            with open(info["backup"], "r", encoding="utf-8") as f:
                old = f.read()
            with open(path, "w", encoding="utf-8") as f:
                f.write(old)
            os.remove(self.last_replacement)
            return "Откатил, сэр. Навык " + info["skill"] + " вернул к прежней версии."
        except Exception:
            return "Откатывать нечего, сэр — недавних замен не было."
